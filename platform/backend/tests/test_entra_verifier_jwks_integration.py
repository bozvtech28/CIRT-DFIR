import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import InvalidTokenError

from app.entra_jwks import build_jwks_resolver
from app.entra_token_verifier import verify_entra_access_token


ISSUER = "https://login.microsoftonline.com/synthetic-tenant/v2.0"
AUDIENCE = "api://synthetic-cirt-dfir"
TENANT = "synthetic-tenant"


@pytest.fixture
def test_material():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    )
    public_jwk.update({
        "kid": "integration-key-1",
        "use": "sig",
        "alg": "RS256",
    })
    return private_key, public_jwk


def make_token(private_key, kid="integration-key-1", **overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "synthetic-integration-user",
        "tid": TENANT,
        "iat": now,
        "nbf": now - timedelta(seconds=2),
        "exp": now + timedelta(minutes=5),
        "roles": ["DFIR Analyst"],
    }
    claims.update(overrides)
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def verify_with_jwks(token, jwks):
    resolver = build_jwks_resolver(jwks)
    return verify_entra_access_token(
        token,
        trusted_key_resolver=resolver,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        expected_tenant_id=TENANT,
    )


def test_valid_token_verifies_through_jwks_and_verifier(test_material):
    private_key, jwk = test_material
    token = make_token(private_key)

    claims = verify_with_jwks(token, {"keys": [jwk]})

    assert claims["sub"] == "synthetic-integration-user"
    assert claims["tid"] == TENANT
    assert claims["roles"] == ["DFIR Analyst"]


def test_invalid_signature_is_rejected(test_material):
    _, trusted_jwk = test_material
    attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = make_token(attacker_key)

    with pytest.raises(InvalidTokenError):
        verify_with_jwks(token, {"keys": [trusted_jwk]})


def test_unknown_kid_is_rejected(test_material):
    private_key, jwk = test_material
    token = make_token(private_key, kid="unknown-key-id")

    with pytest.raises(InvalidTokenError, match="kid"):
        verify_with_jwks(token, {"keys": [jwk]})


def test_expired_token_is_rejected(test_material):
    private_key, jwk = test_material
    old = datetime.now(timezone.utc) - timedelta(minutes=10)
    token = make_token(
        private_key,
        exp=old,
        iat=old - timedelta(minutes=5),
        nbf=old - timedelta(minutes=5),
    )

    with pytest.raises(InvalidTokenError):
        verify_with_jwks(token, {"keys": [jwk]})


def test_wrong_issuer_is_rejected(test_material):
    private_key, jwk = test_material
    token = make_token(private_key, iss="https://untrusted.invalid/")

    with pytest.raises(InvalidTokenError):
        verify_with_jwks(token, {"keys": [jwk]})


def test_wrong_audience_is_rejected(test_material):
    private_key, jwk = test_material
    token = make_token(private_key, aud="api://wrong-audience")

    with pytest.raises(InvalidTokenError):
        verify_with_jwks(token, {"keys": [jwk]})


def test_wrong_tenant_is_rejected(test_material):
    private_key, jwk = test_material
    token = make_token(private_key, tid="another-synthetic-tenant")

    with pytest.raises(InvalidTokenError):
        verify_with_jwks(token, {"keys": [jwk]})


def test_not_before_in_future_is_rejected(test_material):
    private_key, jwk = test_material
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    token = make_token(
        private_key,
        nbf=future,
        exp=future + timedelta(minutes=5),
    )

    with pytest.raises(InvalidTokenError):
        verify_with_jwks(token, {"keys": [jwk]})


def test_rotation_overlap_accepts_old_and_new_keys():
    old_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    new_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    old_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(old_private.public_key())
    )
    old_jwk.update({"kid": "old-key", "use": "sig", "alg": "RS256"})

    new_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(new_private.public_key())
    )
    new_jwk.update({"kid": "new-key", "use": "sig", "alg": "RS256"})

    jwks = {"keys": [old_jwk, new_jwk]}

    old_claims = verify_with_jwks(
        make_token(old_private, kid="old-key"), jwks
    )
    new_claims = verify_with_jwks(
        make_token(new_private, kid="new-key"), jwks
    )

    assert old_claims["sub"] == "synthetic-integration-user"
    assert new_claims["sub"] == "synthetic-integration-user"


def test_removed_key_is_rejected_after_rotation():
    old_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    new_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    new_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(new_private.public_key())
    )
    new_jwk.update({"kid": "new-key", "use": "sig", "alg": "RS256"})

    token = make_token(old_private, kid="old-key")

    with pytest.raises(InvalidTokenError, match="kid"):
        verify_with_jwks(token, {"keys": [new_jwk]})


def test_private_key_material_in_jwks_is_rejected(test_material):
    _, jwk = test_material
    malicious_document = dict(jwk)
    malicious_document["d"] = "not-accepted"

    with pytest.raises(ValueError, match="Private"):
        build_jwks_resolver({"keys": [malicious_document]})


def test_missing_tenant_configuration_fails_closed(test_material):
    private_key, jwk = test_material
    token = make_token(private_key)
    resolver = build_jwks_resolver({"keys": [jwk]})

    with pytest.raises(ValueError, match="expected_tenant_id"):
        verify_entra_access_token(
            token,
            trusted_key_resolver=resolver,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            expected_tenant_id="",
        )
