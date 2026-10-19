import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from synthetic_test_support.rs256_harness import (
    SyntheticRS256Error,
    issue_rs256_token,
    verify_rs256_token,
)

ISSUER = "https://issuer.synthetic.invalid/"
AUDIENCE = "cirt-dfir-synthetic-api"
NOW = 1_800_000_000

# Ephemeral synthetic keys, generated only for this test process.
PRIVATE_A = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_B = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_A = PRIVATE_A.public_key()
PUBLIC_B = PRIVATE_B.public_key()


def claims(**updates):
    result = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "synthetic-rs256-user",
        "iat": NOW - 10,
        "exp": NOW + 300,
    }
    result.update(updates)
    return result


def issue(value=None, kid="key-a", private_key=PRIVATE_A):
    return issue_rs256_token(
        claims() if value is None else value,
        kid=kid,
        private_key=private_key,
    )


def verify(token, keys=None):
    return verify_rs256_token(
        token,
        public_keys_by_kid={"key-a": PUBLIC_A} if keys is None else keys,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        now=NOW,
    )


def test_valid_rs256_token_is_accepted():
    assert verify(issue())["sub"] == "synthetic-rs256-user"


def test_expired_token_is_rejected():
    with pytest.raises(SyntheticRS256Error, match="Expired"):
        verify(issue(claims(exp=NOW - 1)))


def test_wrong_issuer_is_rejected():
    with pytest.raises(SyntheticRS256Error, match="issuer"):
        verify(issue(claims(iss="https://wrong.synthetic.invalid/")))


def test_wrong_audience_is_rejected():
    with pytest.raises(SyntheticRS256Error, match="audience"):
        verify(issue(claims(aud="wrong-api")))


def test_signature_tampering_is_rejected():
    token = issue()
    h, p, sig = token.split(".")
    changed = ("A" if sig[0] != "A" else "B") + sig[1:]
    with pytest.raises(SyntheticRS256Error, match="signature"):
        verify(f"{h}.{p}.{changed}")


def test_payload_tampering_is_rejected():
    token = issue()
    h, p, sig = token.split(".")
    payload = json.loads(
        base64.urlsafe_b64decode(p + "=" * ((4 - len(p) % 4) % 4))
    )
    payload["sub"] = "tampered-user"
    changed_p = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    with pytest.raises(SyntheticRS256Error, match="signature"):
        verify(f"{h}.{changed_p}.{sig}")


def test_unknown_key_id_is_rejected():
    with pytest.raises(SyntheticRS256Error, match="Unknown signing key"):
        verify(issue(kid="untrusted-key"))


def test_key_rotation_overlap_accepts_both_trusted_keys():
    old = issue(kid="key-a", private_key=PRIVATE_A)
    new = issue(kid="key-b", private_key=PRIVATE_B)
    overlap = {"key-a": PUBLIC_A, "key-b": PUBLIC_B}
    assert verify(old, overlap)["sub"] == "synthetic-rs256-user"
    assert verify(new, overlap)["sub"] == "synthetic-rs256-user"


def test_removed_key_is_rejected():
    old = issue(kid="key-a", private_key=PRIVATE_A)
    with pytest.raises(SyntheticRS256Error, match="Unknown signing key"):
        verify(old, {"key-b": PUBLIC_B})


def test_disallowed_algorithm_is_rejected():
    token = issue()
    h, p, sig = token.split(".")
    header = json.loads(
        base64.urlsafe_b64decode(h + "=" * ((4 - len(h) % 4) % 4))
    )
    header["alg"] = "HS256"
    changed_h = base64.urlsafe_b64encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    with pytest.raises(SyntheticRS256Error, match="Disallowed algorithm"):
        verify(f"{changed_h}.{p}.{sig}")


def test_future_not_before_is_rejected():
    with pytest.raises(SyntheticRS256Error, match="not yet valid"):
        verify(issue(claims(nbf=NOW + 60)))


def test_missing_subject_is_rejected():
    value = claims()
    del value["sub"]
    with pytest.raises(SyntheticRS256Error, match="Missing subject"):
        verify(issue(value))


def test_malformed_token_is_rejected():
    with pytest.raises(SyntheticRS256Error, match="Malformed token"):
        verify("not-a-token")
