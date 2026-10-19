"""Provider-neutral OIDC claim checks.

SECURITY BOUNDARY:
validate_verified_claims() does NOT verify JWT signatures.
Call it only with claims returned by a trusted OIDC/JWT verifier that has
already checked the signature, permitted algorithm, issuer metadata/JWKS,
and token integrity. Never pass decoded, unverified JWT payloads here.

Real authentication remains disabled until a provider-specific verifier
is approved, configured, integrated, and tested.
"""
from collections.abc import Mapping
from typing import Any
import time


class InvalidOIDCClaims(ValueError):
    """Raised when already-verified token claims fail required checks."""


def validate_verified_claims(
    claims: Mapping[str, Any],
    *,
    expected_issuer: str,
    expected_audience: str,
    now: float | None = None,
) -> dict[str, Any]:
    """Validate required OIDC claims after cryptographic token verification."""
    if not isinstance(claims, Mapping):
        raise InvalidOIDCClaims("Token claims must be a mapping.")

    if not expected_issuer or not expected_audience:
        raise ValueError("Expected issuer and audience must be configured.")

    issuer = claims.get("iss")
    if not isinstance(issuer, str) or issuer != expected_issuer:
        raise InvalidOIDCClaims("Token issuer is invalid.")

    audience = claims.get("aud")
    if isinstance(audience, str):
        audiences = [audience]
    elif isinstance(audience, list) and all(
        isinstance(item, str) and item for item in audience
    ):
        audiences = audience
    else:
        raise InvalidOIDCClaims("Token audience is missing or malformed.")

    if expected_audience not in audiences:
        raise InvalidOIDCClaims("Token audience is invalid.")

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise InvalidOIDCClaims("Token subject is missing.")

    expiry = claims.get("exp")
    if isinstance(expiry, bool) or not isinstance(expiry, (int, float)):
        raise InvalidOIDCClaims("Token expiry is missing or malformed.")

    current_time = time.time() if now is None else now
    if expiry <= current_time:
        raise InvalidOIDCClaims("Token has expired.")

    if "nbf" in claims:
        not_before = claims["nbf"]
        if isinstance(not_before, bool) or not isinstance(not_before, (int, float)):
            raise InvalidOIDCClaims("Token not-before claim is malformed.")
        if not_before > current_time:
            raise InvalidOIDCClaims("Token is not yet valid.")

    # Return a copy; do not manufacture roles or trust client-provided role data.
    return dict(claims)
