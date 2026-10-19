import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.entra_authenticator import (
    EntraAuthConfig,
    create_entra_authenticator,
)
from app.entra_bearer_adapter import BearerAuthenticationError
from app.entra_metadata_client import MetadataTrustError
from app.security import ROLE_ADMINISTRATOR, ROLE_ANALYST, ROLE_VIEWER


TENANT = "11111111-2222-4333-8444-555555555555"
ISSUER = f"https://login.microsoftonline.com/{TENANT}/v2.0"
AUDIENCE = "api://synthetic-cirt-dfir-api"
DISCOVERY_URL = (
    f"https://login.microsoftonline.com/{TENANT}/v2.0/"
    ".well-known/openid-configuration"
)
JWKS_URI = (
    f"https://login.microsoftonline.com/{TENANT}/discovery/v2.0/keys"
)
HOSTS = frozenset({"login.microsoftonline.com"})
ROLE_MAP = {
    "CIRT.DFIR.Viewer": ROLE_VIEWER,
    "CIRT.DFIR.Analyst": ROLE_ANALYST,
    "CIRT.DFIR.Administrator": ROLE_ADMINISTRATOR,
}


@pytest.fixture
def identity():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    )
    public_jwk.update({
        "kid": "synthetic-composition-key",
        "use": "sig",
        "alg": "RS256",
    })

    def issue_token(roles=None, **overrides):
        now = int(time.time())
        claims = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "synthetic-composition-user",
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
            headers={"kid": "synthetic-composition-key"},
        )

    return public_jwk, issue_token


def make_config(**overrides):
    values = {
        "tenant_id": TENANT,
        "expected_issuer": ISSUER,
        "expected_audience": AUDIENCE,
        "discovery_url": DISCOVERY_URL,
        "trusted_metadata_hosts": HOSTS,
        "allowed_jwks_hosts": HOSTS,
        "approved_role_map": ROLE_MAP,
    }
    values.update(overrides)
    return EntraAuthConfig(**values)


def make_fetcher(public_jwk, calls=None, *, fail_jwks=False, wrong_issuer=False):
    calls = calls if calls is not None else []

    def fetch(url, *, trusted_hosts, timeout_seconds, max_response_bytes):
        calls.append((url, frozenset(trusted_hosts), timeout_seconds, max_response_bytes))
        if url == DISCOVERY_URL:
            issuer = "https://attacker.example/issuer" if wrong_issuer else ISSUER
            return {"issuer": issuer, "jwks_uri": JWKS_URI}
        if url == JWKS_URI:
            if fail_jwks:
                raise OSError("synthetic JWKS outage")
            return {"keys": [public_jwk]}
        raise AssertionError("Unexpected URL requested by composition")

    return fetch


def test_composition_authenticates_valid_synthetic_bearer(identity):
    public_jwk, issue_token = identity
    calls = []
    authenticator = create_entra_authenticator(
        make_config(),
        document_fetcher=make_fetcher(public_jwk, calls),
    )

    # Discovery is loaded at construction; JWKS is loaded on first authentication.
    assert len(calls) == 1
    assert authenticator.metadata.issuer == ISSUER

    principal = authenticator.authenticate("Bearer " + issue_token())

    assert principal.subject == "synthetic-composition-user"
    assert principal.roles == frozenset({ROLE_ANALYST})
    assert len(calls) == 2


def test_composition_rejects_unapproved_application_role(identity):
    public_jwk, issue_token = identity
    authenticator = create_entra_authenticator(
        make_config(),
        document_fetcher=make_fetcher(public_jwk),
    )

    with pytest.raises(BearerAuthenticationError):
        authenticator.authenticate(
            "Bearer " + issue_token(roles=["CIRT.DFIR.SuperUser"])
        )


def test_composition_rejects_wrong_audience(identity):
    public_jwk, issue_token = identity
    authenticator = create_entra_authenticator(
        make_config(),
        document_fetcher=make_fetcher(public_jwk),
    )

    with pytest.raises(BearerAuthenticationError):
        authenticator.authenticate(
            "Bearer " + issue_token(aud="api://wrong-synthetic-audience")
        )


def test_composition_rejects_wrong_tenant(identity):
    public_jwk, issue_token = identity
    authenticator = create_entra_authenticator(
        make_config(),
        document_fetcher=make_fetcher(public_jwk),
    )

    with pytest.raises(BearerAuthenticationError):
        authenticator.authenticate(
            "Bearer " + issue_token(tid="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
        )


def test_composition_rejects_untrusted_discovery_issuer(identity):
    public_jwk, _ = identity

    with pytest.raises(MetadataTrustError):
        create_entra_authenticator(
            make_config(),
            document_fetcher=make_fetcher(public_jwk, wrong_issuer=True),
        )


def test_composition_rejects_discovery_host_not_allowlisted():
    with pytest.raises(ValueError, match="trusted_metadata_hosts"):
        make_config(
            discovery_url="https://attacker.example/.well-known/openid-configuration"
        )


def test_invalid_header_does_not_load_jwks(identity):
    public_jwk, _ = identity
    calls = []
    authenticator = create_entra_authenticator(
        make_config(),
        document_fetcher=make_fetcher(public_jwk, calls),
    )

    with pytest.raises(BearerAuthenticationError):
        authenticator.authenticate("Basic not-a-bearer-token")

    assert len(calls) == 1  # discovery only; no JWKS request


def test_jwks_outage_fails_closed(identity):
    public_jwk, issue_token = identity
    authenticator = create_entra_authenticator(
        make_config(),
        document_fetcher=make_fetcher(public_jwk, fail_jwks=True),
    )

    with pytest.raises(BearerAuthenticationError):
        authenticator.authenticate("Bearer " + issue_token())


def test_role_map_is_copied_and_immutable():
    source = dict(ROLE_MAP)
    config = make_config(approved_role_map=source)
    source.clear()

    assert "CIRT.DFIR.Analyst" in config.approved_role_map
    with pytest.raises(TypeError):
        config.approved_role_map["CIRT.DFIR.SuperUser"] = ROLE_ADMINISTRATOR


@pytest.mark.parametrize(
    "overrides",
    [
        {"tenant_id": ""},
        {"expected_issuer": ""},
        {"expected_audience": ""},
        {"discovery_url": "http://login.microsoftonline.com/discovery"},
        {"trusted_metadata_hosts": frozenset()},
        {"allowed_jwks_hosts": frozenset()},
        {"approved_role_map": {}},
        {"approved_role_map": {"CIRT.DFIR.Analyst": "SuperUser"}},
        {"jwks_ttl_seconds": 0},
        {"timeout_seconds": 11},
        {"max_response_bytes": 0},
    ],
)
def test_invalid_configuration_is_rejected(overrides):
    with pytest.raises(ValueError):
        make_config(**overrides)