from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import InvalidTokenError

from app.entra_token_verifier import verify_entra_access_token


ISSUER = "https://login.microsoftonline.com/synthetic-tenant/v2.0"
AUDIENCE = "api://synthetic-cirt-dfir"
TENANT = "synthetic-tenant"
OTHER_TENANT = "another-synthetic-tenant"


@pytest.fixture
def signing_material():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def make_token(private_key, **overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "synthetic-user-001",
        "tid": TENANT,
        "iat": now,
        "nbf": now - timedelta(seconds=5),
        "exp": now + timedelta(minutes=5),
        "roles": ["DFIR Analyst"],
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "synthetic-key-1"})


def verify(token, public_key):
    return verify_entra_access_token(
        token,
        trusted_key_resolver=lambda _token: public_key,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        expected_tenant_id=TENANT,
    )


def test_accepts_valid_synthetic_rs256_token(signing_material):
    private_key, public_key = signing_material
    claims = verify(make_token(private_key), public_key)
    assert claims["sub"] == "synthetic-user-001"


def test_rejects_tampered_signature(signing_material):
    private_key, public_key = signing_material
    token = make_token(private_key)
    parts = token.split(".")
    parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
    with pytest.raises(InvalidTokenError):
        verify(".".join(parts), public_key)


def test_rejects_expired_token(signing_material):
    private_key, public_key = signing_material
    old = datetime.now(timezone.utc) - timedelta(minutes=10)
    token = make_token(private_key, exp=old, iat=old - timedelta(minutes=5), nbf=old - timedelta(minutes=5))
    with pytest.raises(InvalidTokenError):
        verify(token, public_key)


def test_rejects_wrong_issuer(signing_material):
    private_key, public_key = signing_material
    with pytest.raises(InvalidTokenError):
        verify(make_token(private_key, iss="https://untrusted.invalid/"), public_key)


def test_rejects_wrong_audience(signing_material):
    private_key, public_key = signing_material
    with pytest.raises(InvalidTokenError):
        verify(make_token(private_key, aud="api://wrong-audience"), public_key)


def test_rejects_wrong_tenant(signing_material):
    private_key, public_key = signing_material
    with pytest.raises(InvalidTokenError):
        verify(make_token(private_key, tid=OTHER_TENANT), public_key)


def test_rejects_token_signed_by_another_key(signing_material):
    private_key, _ = signing_material
    other_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(InvalidTokenError):
        verify(make_token(private_key), other_private.public_key())


def test_rejects_hs256_token(signing_material):
    private_key, public_key = signing_material
    token = jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "sub": "synthetic-user",
         "tid": TENANT, "iat": 1, "nbf": 1, "exp": 4102444800},
        "synthetic-test-secret-at-least-32-bytes-long",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        verify(token, public_key)


def test_rejects_missing_subject(signing_material):
    private_key, public_key = signing_material
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "tid": TENANT,
        "iat": now,
        "nbf": now - timedelta(seconds=1),
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    with pytest.raises(InvalidTokenError):
        verify(token, public_key)

def test_rejects_missing_required_exp_claim(signing_material):
    private_key, public_key = signing_material
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER, "aud": AUDIENCE, "sub": "synthetic-user-001",
        "tid": TENANT, "iat": now, "nbf": now - timedelta(seconds=1),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    with pytest.raises(InvalidTokenError):
        verify(token, public_key)


def test_requires_configured_tenant(signing_material):
    private_key, public_key = signing_material
    token = make_token(private_key)
    with pytest.raises(ValueError):
        verify_entra_access_token(
            token,
            trusted_key_resolver=lambda _token: public_key,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            expected_tenant_id="",
        )


def test_rejects_empty_token(signing_material):
    _, public_key = signing_material
    with pytest.raises(InvalidTokenError):
        verify("", public_key)

