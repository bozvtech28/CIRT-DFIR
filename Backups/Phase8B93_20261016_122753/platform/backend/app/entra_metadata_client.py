"""Provider-neutral Entra metadata/JWKS client primitives.

This module intentionally performs no network I/O.
A caller must inject a trusted transport and must validate the
approved tenant, issuer, discovery endpoint, and JWKS URI.

Do not use token-provided URLs to select a metadata endpoint.
This module is not wired into the production authentication gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse


class MetadataTrustError(ValueError):
    """Raised when discovery metadata or JWKS data is not trusted."""


@dataclass(frozen=True)
class TrustedMetadata:
    issuer: str
    jwks_uri: str


def _require_https_url(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MetadataTrustError(f"{field_name} must be a non-empty URL")

    parsed = urlparse(value)

    if parsed.scheme.lower() != "https":
        raise MetadataTrustError(f"{field_name} must use HTTPS")
    if not parsed.hostname:
        raise MetadataTrustError(f"{field_name} must include a hostname")
    if parsed.username or parsed.password:
        raise MetadataTrustError(f"{field_name} must not contain URL credentials")
    if parsed.fragment:
        raise MetadataTrustError(f"{field_name} must not contain a fragment")

    return value


def validate_discovery_document(
    document: Any,
    *,
    expected_issuer: str,
    allowed_jwks_hosts: set[str],
) -> TrustedMetadata:
    """Validate discovery metadata against caller-approved trust settings.

    The caller is responsible for obtaining the document from the
    approved, fixed discovery URL over a trusted HTTPS transport.
    """

    if not isinstance(document, dict):
        raise MetadataTrustError("Discovery document must be a JSON object")

    if not isinstance(expected_issuer, str) or not expected_issuer.strip():
        raise MetadataTrustError("Expected issuer is not configured")

    issuer = document.get("issuer")
    jwks_uri = document.get("jwks_uri")

    if not isinstance(issuer, str) or issuer != expected_issuer:
        raise MetadataTrustError("Discovery issuer does not match configuration")

    _require_https_url(issuer, "issuer")
    _require_https_url(jwks_uri, "jwks_uri")

    parsed_jwks = urlparse(jwks_uri)
    allowed_hosts = {
        host.lower().rstrip(".")
        for host in allowed_jwks_hosts
        if isinstance(host, str) and host.strip()
    }

    if (parsed_jwks.hostname or "").lower().rstrip(".") not in allowed_hosts:
        raise MetadataTrustError("JWKS hostname is not in the approved allowlist")

    if parsed_jwks.query:
        raise MetadataTrustError("JWKS URI query parameters are not allowed")
    if parsed_jwks.fragment:
        raise MetadataTrustError("JWKS URI fragments are not allowed")

    return TrustedMetadata(issuer=issuer, jwks_uri=jwks_uri)


def fetch_trusted_document(
    url: str,
    *,
    trusted_hosts: set[str],
    transport: Callable[[str, float], Any],
    timeout_seconds: float = 3.0,
) -> Any:
    """Use an injected transport to fetch JSON from an allowlisted HTTPS host.

    The injected transport must enforce the timeout and validate every
    redirect destination. This function never follows redirects itself.
    """

    _require_https_url(url, "request URL")

    if timeout_seconds <= 0 or timeout_seconds > 10:
        raise MetadataTrustError("Timeout must be greater than 0 and at most 10 seconds")

    host = (urlparse(url).hostname or "").lower().rstrip(".")
    allowed = {
        item.lower().rstrip(".")
        for item in trusted_hosts
        if isinstance(item, str) and item.strip()
    }

    if host not in allowed:
        raise MetadataTrustError("Request hostname is not in the approved allowlist")

    result = transport(url, timeout_seconds)

    if not isinstance(result, dict):
        raise MetadataTrustError("Transport must return a decoded JSON object")

    return result


def validate_jwks_document(document: Any) -> dict[str, Any]:
    """Perform structural checks before the existing offline JWKS resolver."""

    if not isinstance(document, dict):
        raise MetadataTrustError("JWKS document must be a JSON object")

    keys = document.get("keys")
    if not isinstance(keys, list) or not keys:
        raise MetadataTrustError("JWKS must contain a non-empty keys array")

    seen_kids: set[str] = set()

    for key in keys:
        if not isinstance(key, dict):
            raise MetadataTrustError("Each JWKS key must be a JSON object")

        kid = key.get("kid")
        if not isinstance(kid, str) or not kid.strip():
            raise MetadataTrustError("Each JWKS key must have a non-empty kid")

        if kid in seen_kids:
            raise MetadataTrustError("JWKS contains duplicate key IDs")
        seen_kids.add(kid)

        if key.get("kty") != "RSA":
            raise MetadataTrustError("Only RSA signing keys are accepted")
        if key.get("use", "sig") != "sig":
            raise MetadataTrustError("JWKS key must be designated for signatures")
        if key.get("alg", "RS256") != "RS256":
            raise MetadataTrustError("Only RS256 signing keys are accepted")

        private_parameters = {"d", "p", "q", "dp", "dq", "qi", "oth"}
        if private_parameters.intersection(key):
            raise MetadataTrustError("JWKS must not contain private key parameters")

        if not isinstance(key.get("n"), str) or not key["n"]:
            raise MetadataTrustError("RSA key modulus is missing")
        if not isinstance(key.get("e"), str) or not key["e"]:
            raise MetadataTrustError("RSA key exponent is missing")

    return document