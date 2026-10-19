import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.entra_bearer_adapter import (
    BearerAuthenticationError,
    principal_from_authorization_header,
)
from app.entra_jwks import build_jwks_resolver
from app.security import (
    ROLE_ADMINISTRATOR,
    ROLE_ANALYST,
    ROLE_VIEWER,
    AuthorizationDenied,
    authorize,
)

TENANT = "11111111-2222-4333-8444-555555555555"
ISSUER = f"https://login.microsoftonline.com/{TENANT}/v2.0"
AUDIENCE = "api://synthetic-cirt-dfir-api"
ROLE_MAP = {
    "CIRT.DFIR.Viewer": ROLE_VIEWER,
    "CIRT.DFIR.Analyst": ROLE_ANALYST,
    "CIRT.DFIR.Administrator": ROLE_ADMINISTRATOR,
}


@pytest.fixture
def identity():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    )
    public_jwk.update({
        "kid": "offline-adapter-test-key",
        "use": "sig",
        "alg": "RS256",
    })
    resolver = build_jwks_resolver({"keys": [public_jwk]})

    def issue_token(roles=None, **overrides):
        now = int(time.time())
        claims = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "synthetic-adapter-user",
            "tid": TENANT,
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
            headers={"kid": "offline-adapter-test-key"},
        )

    return resolver, issue_token


def authenticate(header, resolver):
    return principal_from_authorization_header(
        header,
        trusted_key_resolver=resolver,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        expected_tenant_id=TENANT,
        approved_role_map=ROLE_MAP,
    )


def test_valid_analyst_bearer_produces_principal(identity):
    resolver, issue = identity
    principal = authenticate("Bearer " + issue(), resolver)
    assert principal.subject == "synthetic-adapter-user"
    assert principal.roles == frozenset({ROLE_ANALYST})
    assert authorize(principal, "cases:read")
    assert authorize(principal, "cases:update")


def test_viewer_cannot_update(identity):
    resolver, issue = identity
    principal = authenticate(
        "Bearer " + issue(roles=["CIRT.DFIR.Viewer"]),
        resolver,
    )
    with pytest.raises(AuthorizationDenied):
        authorize(principal, "cases:update")


def test_administrator_can_pass_admin_permission(identity):
    resolver, issue = identity
    principal = authenticate(
        "Bearer " + issue(roles=["CIRT.DFIR.Administrator"]),
        resolver,
    )
    assert authorize(principal, "users:manage")
    assert authorize(principal, "audit:read")


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "Basic abc",
        "Bearer",
        "Bearer ",
        "Bearer first second",
    ],
)
def test_missing_or_malformed_header_is_rejected(identity, header):
    resolver, _ = identity
    with pytest.raises(BearerAuthenticationError):
        authenticate(header, resolver)


def test_tampered_token_is_rejected(identity):
    resolver, issue = identity
    token = issue()
    header, payload, signature = token.split(".")
    altered = ("A" if signature[0] != "A" else "B") + signature[1:]
    with pytest.raises(BearerAuthenticationError):
        authenticate(f"Bearer {header}.{payload}.{altered}", resolver)


def test_wrong_tenant_is_rejected(identity):
    resolver, issue = identity
    with pytest.raises(BearerAuthenticationError):
        authenticate(
            "Bearer " + issue(tid="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"),
            resolver,
        )


def test_unapproved_role_is_rejected(identity):
    resolver, issue = identity
    with pytest.raises(BearerAuthenticationError):
        authenticate(
            "Bearer " + issue(roles=["CIRT.DFIR.Unapproved"]),
            resolver,
        )


def test_empty_roles_are_rejected(identity):
    resolver, issue = identity
    with pytest.raises(BearerAuthenticationError):
        authenticate("Bearer " + issue(roles=[]), resolver)
