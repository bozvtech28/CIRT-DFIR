import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import InvalidTokenError

from app.entra_jwks import build_jwks_resolver


def make_pair(kid):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return private_key, public_jwk


def make_token(private_key, kid="key-a", algorithm="RS256"):
    return jwt.encode(
        {"sub": "synthetic-user", "iat": 1800000000, "nbf": 1800000000, "exp": 4102444800},
        private_key,
        algorithm=algorithm,
        headers={"kid": kid},
    )


def test_selects_matching_key_from_jwks():
    private_key, public_jwk = make_pair("key-a")
    resolver = build_jwks_resolver({"keys": [public_jwk]})
    token = make_token(private_key, "key-a")
    selected = resolver(token)
    decoded = jwt.decode(
        token,
        selected,
        algorithms=["RS256"],
        options={"verify_exp": False, "verify_iat": False, "verify_nbf": False},
    )
    assert decoded["sub"] == "synthetic-user"


def test_selects_correct_key_when_multiple_keys_exist():
    private_a, jwk_a = make_pair("key-a")
    _, jwk_b = make_pair("key-b")
    resolver = build_jwks_resolver({"keys": [jwk_a, jwk_b]})
    assert resolver(make_token(private_a, "key-a")) is not None


def test_rejects_unknown_kid():
    _, jwk = make_pair("known-key")
    resolver = build_jwks_resolver({"keys": [jwk]})
    unrelated_private, _ = make_pair("unknown-key")
    with pytest.raises(InvalidTokenError, match="kid"):
        resolver(make_token(unrelated_private, "unknown-key"))


def test_supports_rotation_overlap_with_old_and_new_keys():
    old_private, old_jwk = make_pair("old-key")
    new_private, new_jwk = make_pair("new-key")
    resolver = build_jwks_resolver({"keys": [old_jwk, new_jwk]})
    assert resolver(make_token(old_private, "old-key")) is not None
    assert resolver(make_token(new_private, "new-key")) is not None


def test_removed_key_is_rejected_after_rotation():
    old_private, old_jwk = make_pair("old-key")
    _, new_jwk = make_pair("new-key")
    resolver_after_rotation = build_jwks_resolver({"keys": [new_jwk]})
    with pytest.raises(InvalidTokenError, match="kid"):
        resolver_after_rotation(make_token(old_private, "old-key"))


@pytest.mark.parametrize("document", [
    None,
    {},
    {"keys": []},
    {"keys": "not-a-list"},
])
def test_rejects_malformed_jwks_documents(document):
    with pytest.raises(ValueError):
        build_jwks_resolver(document)


def test_rejects_duplicate_kids():
    _, jwk_a = make_pair("duplicate")
    _, jwk_b = make_pair("duplicate")
    with pytest.raises(ValueError, match="Duplicate"):
        build_jwks_resolver({"keys": [jwk_a, jwk_b]})


def test_rejects_non_rsa_key():
    with pytest.raises(ValueError, match="RSA"):
        build_jwks_resolver({"keys": [{"kid": "ec-key", "kty": "EC"}]})


def test_rejects_encryption_only_key():
    _, jwk = make_pair("enc-key")
    jwk["use"] = "enc"
    with pytest.raises(ValueError, match="sig"):
        build_jwks_resolver({"keys": [jwk]})


def test_rejects_non_rs256_jwk():
    _, jwk = make_pair("other-alg")
    jwk["alg"] = "RS384"
    with pytest.raises(ValueError, match="RS256"):
        build_jwks_resolver({"keys": [jwk]})


def test_rejects_private_key_material_in_jwks():
    _, jwk = make_pair("private-key")
    jwk["d"] = "not-accepted"
    with pytest.raises(ValueError, match="Private"):
        build_jwks_resolver({"keys": [jwk]})


def test_rejects_token_without_kid():
    private_key, jwk = make_pair("key-a")
    resolver = build_jwks_resolver({"keys": [jwk]})
    token = jwt.encode(
        {"sub": "synthetic-user"},
        private_key,
        algorithm="RS256",
    )
    with pytest.raises(InvalidTokenError, match="kid"):
        resolver(token)


def test_rejects_non_rs256_token_header():
    private_key = "synthetic-test-secret-at-least-32-bytes-long"
    jwk_private, jwk = make_pair("key-a")
    resolver = build_jwks_resolver({"keys": [jwk]})
    token = jwt.encode(
        {"sub": "synthetic-user"},
        private_key,
        algorithm="HS256",
        headers={"kid": "key-a"},
    )
    with pytest.raises(InvalidTokenError, match="RS256"):
        resolver(token)


def test_rejects_malformed_token():
    _, jwk = make_pair("key-a")
    resolver = build_jwks_resolver({"keys": [jwk]})
    with pytest.raises(InvalidTokenError, match="Malformed"):
        resolver("not.a.valid.jwt")
