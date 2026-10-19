"""Offline JWKS key selector for the Entra verifier prototype.

No HTTP calls are made by this module. The JWKS document must come from a
trusted, administrator-approved source before any production use.
This module is not wired into application routes.
"""
from collections.abc import Mapping
from typing import Any

import jwt
from jwt import InvalidTokenError


def build_jwks_resolver(jwks: Mapping[str, Any]):
    """Build a resolver from a supplied JWKS document.

    Intended for offline tests and later integration design. This function
    does not establish that the supplied JWKS document is authentic.
    """
    if not isinstance(jwks, Mapping):
        raise ValueError("JWKS must be a mapping.")

    keys = jwks.get("keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError("JWKS must contain a non-empty keys array.")

    indexed: dict[str, Any] = {}

    for item in keys:
        if not isinstance(item, Mapping):
            raise ValueError("Every JWKS key must be an object.")

        kid = item.get("kid")
        if not isinstance(kid, str) or not kid.strip():
            raise ValueError("Every JWKS key must have a non-empty kid.")

        if kid in indexed:
            raise ValueError("Duplicate kid values are not allowed.")

        if item.get("kty") != "RSA":
            raise ValueError("Only RSA signing keys are supported.")

        if item.get("use", "sig") != "sig":
            raise ValueError("JWKS key use must be sig.")

        if item.get("alg", "RS256") != "RS256":
            raise ValueError("Only RS256 JWKS keys are supported.")

        # A public JWKS must not include RSA private-key parameters.
        if any(name in item for name in ("d", "p", "q", "dp", "dq", "qi", "oth")):
            raise ValueError("Private RSA key material is not accepted.")

        try:
            parsed = jwt.PyJWK.from_dict(dict(item), algorithm="RS256")
            indexed[kid] = parsed.key
        except Exception as exc:
            raise ValueError(f"Invalid RSA JWK for kid {kid!r}.") from exc

    def resolve(token: str):
        try:
            header = jwt.get_unverified_header(token)
        except Exception as exc:
            raise InvalidTokenError("Malformed JWT header.") from exc

        if header.get("alg") != "RS256":
            raise InvalidTokenError("Only RS256 tokens are accepted.")

        kid = header.get("kid")
        if not isinstance(kid, str) or not kid.strip():
            raise InvalidTokenError("JWT header must contain a non-empty kid.")

        key = indexed.get(kid)
        if key is None:
            raise InvalidTokenError("JWT kid was not found in the trusted JWKS set.")

        return key

    return resolve
