"""Offline-tested bearer-token adapter for the CIRT DFIR Entra integration.

This module does not fetch metadata or JWKS and is not wired into FastAPI.
The caller must supply a trusted key resolver and approved server-side config.
"""
from collections.abc import Mapping
from typing import Any

from jwt import InvalidTokenError

from app.entra_principal import (
    PrincipalMappingError,
    principal_from_verified_claims,
)
from app.entra_token_verifier import verify_entra_access_token
from app.security import Principal


class BearerAuthenticationError(Exception):
    """Raised when a bearer token cannot produce a trusted principal."""


def principal_from_authorization_header(
    authorization: str | None,
    *,
    trusted_key_resolver,
    expected_issuer: str,
    expected_audience: str,
    expected_tenant_id: str,
    approved_role_map: Mapping[str, str],
) -> Principal:
    """Validate a Bearer header, verify its JWT, and map verified roles.

    This function deliberately performs no network requests. Do not pass
    untrusted JWKS data or configuration supplied by a browser/request body.
    """
    if not isinstance(authorization, str):
        raise BearerAuthenticationError("A Bearer authorization header is required.")

    scheme, separator, raw_token = authorization.partition(" ")
    token = raw_token.strip()

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token
        or any(character.isspace() for character in token)
    ):
        raise BearerAuthenticationError("The authorization header is malformed.")

    try:
        claims = verify_entra_access_token(
            token,
            trusted_key_resolver=trusted_key_resolver,
            expected_issuer=expected_issuer,
            expected_audience=expected_audience,
            expected_tenant_id=expected_tenant_id,
        )
        return principal_from_verified_claims(
            claims,
            approved_role_map=approved_role_map,
        )
    except (InvalidTokenError, PrincipalMappingError, ValueError) as exc:
        raise BearerAuthenticationError(
            "Bearer token validation or role mapping failed."
        ) from exc
