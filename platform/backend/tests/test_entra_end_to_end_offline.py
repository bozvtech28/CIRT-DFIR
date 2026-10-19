import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import InvalidTokenError

from app.entra_jwks import build_jwks_resolver
from app.entra_principal import (
    PrincipalMappingError,
    principal_from_verified_claims,
)
from app.entra_token_verifier import verify_entra_access_token
from app.security import (
    AuthorizationDenied,
    ROLE_ADMINISTRATOR,
    ROLE_ANALYST,
    ROLE_VIEWER,
    authorize,
)

TENANT_ID = "11111111-2222-4333-8444-555555555555"
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
AUDIENCE = "api://synthetic-cirt-dfir-api"
ROLE_MAP = {
    "CIRT.DFIR.Viewer": ROLE_VIEWER,
    "CIRT.DFIR.Analyst": ROLE_ANALYST,
    "CIRT.DFIR.Administrator": ROLE_ADMINISTRATOR,
}


@pytest.fixture
def identity_material():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    )
    public_jwk.update({
        "kid": "synthetic-test-key",
        "use": "sig",
        "alg": "RS256",
    })
    jwks = {"keys": [public_jwk]}
    resolver = build_jwks_resolver(jwks)
    now = int(time.time())

    def issue_token(roles=None, **overrides):
        claims = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "synthetic-user-001",
            "tid": TENANT_ID,
            "iat": now,
            "nbf": now,
            "exp": now + 300,
            "roles": roles if roles is not None else ["CIRT.DFIR.Analyst"],
        }
        claims.update(overrides)
        return jwt.encode(
            claims,
            private_key,
            algorithm="RS256",
            headers={"kid": "synthetic-test-key"},
        )

    return resolver, issue_token


def verify(token, resolver):
    return verify_entra_access_token(
        token,
        trusted_key_resolver=resolver,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        expected_tenant_id=TENANT_ID,
    )


def test_synthetic_token_verifies_maps_and_authorizes(identity_material):
    resolver, issue_token = identity_material
    claims = verify(issue_token(), resolver)
    principal = principal_from_verified_claims(
        claims,
        approved_role_map=ROLE_MAP,
    )

    assert principal.subject == "synthetic-user-001"
    assert principal.roles == frozenset({ROLE_ANALYST})
    assert authorize(principal, "cases:read")
    assert authorize(principal, "cases:update")

    with pytest.raises(AuthorizationDenied):
        authorize(principal, "users:manage")


def test_viewer_can_read_but_cannot_update(identity_material):
    resolver, issue_token = identity_material
    claims = verify(
        issue_token(roles=["CIRT.DFIR.Viewer"]),
        resolver,
    )
    principal = principal_from_verified_claims(
        claims,
        approved_role_map=ROLE_MAP,
    )

    assert authorize(principal, "cases:read")
    with pytest.raises(AuthorizationDenied):
        authorize(principal, "cases:update")


def test_invalid_signature_is_rejected_before_role_mapping(identity_material):
    resolver, issue_token = identity_material
    token = issue_token()
    header, payload, signature = token.split(".")
    altered_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered_token = f"{header}.{payload}.{altered_signature}"

    with pytest.raises(InvalidTokenError):
        verify(tampered_token, resolver)


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://attacker.invalid/"},
        {"aud": "api://wrong-audience"},
        {"tid": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"},
        {"exp": int(time.time()) - 60},
        {"nbf": int(time.time()) + 600},
    ],
)
def test_invalid_claims_are_rejected(identity_material, overrides):
    resolver, issue_token = identity_material
    with pytest.raises(InvalidTokenError):
        verify(issue_token(**overrides), resolver)


def test_unapproved_role_is_rejected(identity_material):
    resolver, issue_token = identity_material
    claims = verify(
        issue_token(roles=["CIRT.DFIR.Unapproved"]),
        resolver,
    )

    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            claims,
            approved_role_map=ROLE_MAP,
        )


def test_missing_roles_are_rejected(identity_material):
    resolver, issue_token = identity_material
    claims = verify(issue_token(roles=[]), resolver)

    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            claims,
            approved_role_map=ROLE_MAP,
        )
