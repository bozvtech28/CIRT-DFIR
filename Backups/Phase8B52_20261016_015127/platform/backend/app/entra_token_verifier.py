"""Isolated Microsoft Entra access-token verification foundation.

SECURITY BOUNDARY:
- This module is NOT wired into application routes.
- The caller must provide a key resolver backed by trusted Microsoft
  OpenID Connect metadata/JWKS, with HTTPS and safe key-rotation handling.
- Never use a token-provided URL or arbitrary token-provided key as trusted.
- Never use this verifier until tenant, issuer, and audience are approved.
"""
from collections.abc import Callable
from typing import Any

import jwt
from jwt import InvalidTokenError

TrustedKeyResolver = Callable[[str], Any]


def verify_entra_access_token(
    token: str,
    *,
    trusted_key_resolver: TrustedKeyResolver,
    expected_issuer: str,
    expected_audience: str,
    expected_tenant_id: str,
) -> dict[str, Any]:
    """Verify an RS256 token against a trusted key resolver and fixed config.

    The resolver must obtain keys only from an administrator-approved,
    trusted JWKS source. This function deliberately performs no network access.
    """
    if not isinstance(token, str) or not token.strip():
        raise InvalidTokenError("A non-empty bearer token is required.")

    for name, value in (
        ("expected_issuer", expected_issuer),
        ("expected_audience", expected_audience),
        ("expected_tenant_id", expected_tenant_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be configured before verification.")

    if not callable(trusted_key_resolver):
        raise ValueError("A trusted signing-key resolver is required.")

    # The key resolver must select a key from a trusted JWKS source.
    # The token's algorithm is not allowed to select the accepted algorithm.
    signing_key = trusted_key_resolver(token)
    if signing_key is None:
        raise InvalidTokenError("No trusted signing key was found.")

    claims = jwt.decode(
        token,
        key=signing_key,
        algorithms=["RS256"],
        issuer=expected_issuer,
        audience=expected_audience,
        options={
            "require": ["exp", "iat", "nbf", "iss", "aud", "sub", "tid"],
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "verify_nbf": True,
            "verify_iss": True,
            "verify_aud": True,
        },
        leeway=0,
    )

    if not isinstance(claims.get("sub"), str) or not claims["sub"].strip():
        raise InvalidTokenError("The subject claim is missing or invalid.")

    if claims.get("tid") != expected_tenant_id:
        raise InvalidTokenError("The token tenant does not match the configured tenant.")

    return claims
