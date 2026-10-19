import base64
import json

import pytest

from synthetic_test_support.jwt_harness import (
    SyntheticTokenError,
    issue_synthetic_token,
    verify_synthetic_token,
)

ISSUER = "https://issuer.synthetic.invalid/"
AUDIENCE = "cirt-dfir-synthetic-test"
NOW = 1_800_000_000
KEY_A = b"A" * 32
KEY_B = b"B" * 32


def claims(**overrides):
    value = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "synthetic-user-001",
        "iat": NOW - 10,
        "exp": NOW + 300,
    }
    value.update(overrides)
    return value


def issue(value=None, *, kid="test-key-a", key=KEY_A):
    return issue_synthetic_token(
        claims() if value is None else value,
        kid=kid,
        key=key,
    )


def verify(token, keys=None):
    return verify_synthetic_token(
        token,
        keys_by_kid={"test-key-a": KEY_A} if keys is None else keys,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        now=NOW,
    )


def test_valid_synthetic_token_is_accepted():
    assert verify(issue())["sub"] == "synthetic-user-001"


def test_expired_token_is_rejected():
    with pytest.raises(SyntheticTokenError, match="Expired"):
        verify(issue(claims(exp=NOW - 1)))


def test_wrong_issuer_is_rejected():
    with pytest.raises(SyntheticTokenError, match="issuer"):
        verify(issue(claims(iss="https://wrong.synthetic.invalid/")))


def test_wrong_audience_is_rejected():
    with pytest.raises(SyntheticTokenError, match="audience"):
        verify(issue(claims(aud="wrong-api")))


def test_invalid_signature_is_rejected():
    token = issue()
    header, payload, signature = token.split(".")
    changed = ("A" if signature[0] != "A" else "B") + signature[1:]
    with pytest.raises(SyntheticTokenError, match="signature"):
        verify(f"{header}.{payload}.{changed}")


def test_unknown_key_id_is_rejected():
    token = issue(kid="unknown-key")
    with pytest.raises(SyntheticTokenError, match="Unknown signing key"):
        verify(token)


def test_key_rotation_accepts_old_and_new_keys_during_overlap():
    old_token = issue(kid="test-key-a", key=KEY_A)
    new_token = issue(kid="test-key-b", key=KEY_B)
    overlap_keys = {"test-key-a": KEY_A, "test-key-b": KEY_B}
    assert verify(old_token, overlap_keys)["sub"] == "synthetic-user-001"
    assert verify(new_token, overlap_keys)["sub"] == "synthetic-user-001"


def test_removed_old_key_is_rejected_after_rotation():
    old_token = issue(kid="test-key-a", key=KEY_A)
    with pytest.raises(SyntheticTokenError, match="Unknown signing key"):
        verify(old_token, {"test-key-b": KEY_B})


def test_disallowed_algorithm_is_rejected():
    token = issue()
    header, payload, signature = token.split(".")
    decoded = json.loads(
        base64.urlsafe_b64decode(header + "=" * ((4 - len(header) % 4) % 4))
    )
    decoded["alg"] = "none"
    new_header = base64.urlsafe_b64encode(
        json.dumps(decoded, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    with pytest.raises(SyntheticTokenError, match="Disallowed algorithm"):
        verify(f"{new_header}.{payload}.{signature}")


def test_future_not_before_is_rejected():
    with pytest.raises(SyntheticTokenError, match="not yet valid"):
        verify(issue(claims(nbf=NOW + 60)))


def test_malformed_token_is_rejected():
    with pytest.raises(SyntheticTokenError, match="Malformed token"):
        verify("not-a-jwt")


def test_missing_subject_is_rejected():
    value = claims()
    value.pop("sub")
    with pytest.raises(SyntheticTokenError, match="Missing subject"):
        verify(issue(value))
