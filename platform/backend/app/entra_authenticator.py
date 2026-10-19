"""Isolated composition of the CIRT DFIR Microsoft Entra auth primitives.

This module is deliberately NOT wired into FastAPI. Configuration must be
approved by the deployment owner and supplied explicitly by trusted code.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable
from urllib.parse import urlparse

from jwt import InvalidTokenError

from app.entra_bearer_adapter import (
    BearerAuthenticationError,
    principal_from_authorization_header,
)
from app.entra_http_transport import fetch_json_document
from app.entra_jwks import build_jwks_resolver
from app.entra_jwks_cache import JWKSCache, JWKSCacheError
from app.entra_metadata_client import (
    MetadataTrustError,
    TrustedMetadata,
    fetch_trusted_document,
    validate_discovery_document,
)
from app.security import KNOWN_ROLES, Principal


DocumentFetcher = Callable[..., dict[str, Any]]


def _normalized_hosts(value: frozenset[str], field_name: str) -> frozenset[str]:
    if not isinstance(value, (set, frozenset)) or not value:
        raise ValueError(f"{field_name} must be a non-empty set of hostnames")

    hosts: set[str] = set()
    for host in value:
        if not isinstance(host, str) or not host.strip():
            raise ValueError(f"{field_name} contains an invalid hostname")
        normalized = host.strip().lower().rstrip(".")
        if "/" in normalized or ":" in normalized or "@" in normalized:
            raise ValueError(f"{field_name} must contain hostnames, not URLs")
        hosts.add(normalized)

    if not hosts:
        raise ValueError(f"{field_name} must not be empty")
    return frozenset(hosts)


@dataclass(frozen=True)
class EntraAuthConfig:
    """Explicit server-side trust configuration; never build from request data."""

    tenant_id: str
    expected_issuer: str
    expected_audience: str
    discovery_url: str
    trusted_metadata_hosts: frozenset[str]
    allowed_jwks_hosts: frozenset[str]
    approved_role_map: Mapping[str, str]
    jwks_ttl_seconds: float = 300.0
    timeout_seconds: float = 3.0
    max_response_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "expected_issuer",
            "expected_audience",
            "discovery_url",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be explicitly configured")

        try:
            issuer = urlparse(self.expected_issuer)
            issuer_port = issuer.port
        except ValueError as exc:
            raise ValueError("expected_issuer is malformed") from exc

        if (
            issuer.scheme.lower() != "https"
            or not issuer.hostname
            or issuer_port not in (None, 443)
            or issuer.username
            or issuer.password
            or issuer.query
            or issuer.fragment
        ):
            raise ValueError("expected_issuer must be a fixed, safe HTTPS URL")

        try:
            parsed = urlparse(self.discovery_url)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("discovery_url is malformed") from exc

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or port not in (None, 443)
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("discovery_url must be a fixed, safe HTTPS URL")

        metadata_hosts = _normalized_hosts(
            self.trusted_metadata_hosts, "trusted_metadata_hosts"
        )
        jwks_hosts = _normalized_hosts(
            self.allowed_jwks_hosts, "allowed_jwks_hosts"
        )

        if parsed.hostname.lower().rstrip(".") not in metadata_hosts:
            raise ValueError("discovery_url host is not in trusted_metadata_hosts")

        if not isinstance(self.approved_role_map, Mapping) or not self.approved_role_map:
            raise ValueError("approved_role_map must be a non-empty mapping")

        role_map: dict[str, str] = {}
        for app_role, internal_role in self.approved_role_map.items():
            if not isinstance(app_role, str) or not app_role.strip():
                raise ValueError("Application role names must be non-empty strings")
            if not isinstance(internal_role, str) or internal_role not in KNOWN_ROLES:
                raise ValueError("Role map contains an unrecognized internal role")
            role_map[app_role] = internal_role

        if not isinstance(self.jwks_ttl_seconds, (int, float)) or isinstance(
            self.jwks_ttl_seconds, bool
        ):
            raise ValueError("jwks_ttl_seconds must be numeric")
        if not 0 < self.jwks_ttl_seconds <= 3600:
            raise ValueError("jwks_ttl_seconds must be greater than 0 and at most 3600")

        if not isinstance(self.timeout_seconds, (int, float)) or isinstance(
            self.timeout_seconds, bool
        ):
            raise ValueError("timeout_seconds must be numeric")
        if not 0 < self.timeout_seconds <= 10:
            raise ValueError("timeout_seconds must be greater than 0 and at most 10")

        if not isinstance(self.max_response_bytes, int) or isinstance(
            self.max_response_bytes, bool
        ):
            raise ValueError("max_response_bytes must be an integer")
        if not 1 <= self.max_response_bytes <= 4 * 1024 * 1024:
            raise ValueError("max_response_bytes must be between 1 byte and 4 MiB")

        object.__setattr__(self, "trusted_metadata_hosts", metadata_hosts)
        object.__setattr__(self, "allowed_jwks_hosts", jwks_hosts)
        object.__setattr__(self, "approved_role_map", MappingProxyType(role_map))


class EntraAuthenticator:
    """Authenticate bearer headers using the explicitly approved configuration."""

    def __init__(
        self,
        config: EntraAuthConfig,
        metadata: TrustedMetadata,
        jwks_cache: JWKSCache,
    ) -> None:
        self._config = config
        self._metadata = metadata
        self._jwks_cache = jwks_cache

    @property
    def metadata(self) -> TrustedMetadata:
        """Expose the validated issuer/JWKS URI, not unvalidated discovery data."""
        return self._metadata

    def _trusted_key_resolver(self, token: str):
        try:
            document = self._jwks_cache.get()
            resolver = build_jwks_resolver(document)
            return resolver(token)
        except JWKSCacheError as exc:
            # The adapter converts InvalidTokenError into a generic auth failure.
            raise InvalidTokenError("Trusted signing keys are unavailable.") from exc

    def authenticate(self, authorization: str | None) -> Principal:
        """Return a principal only after complete token and role validation."""
        return principal_from_authorization_header(
            authorization,
            trusted_key_resolver=self._trusted_key_resolver,
            expected_issuer=self._config.expected_issuer,
            expected_audience=self._config.expected_audience,
            expected_tenant_id=self._config.tenant_id,
            approved_role_map=self._config.approved_role_map,
        )


def create_entra_authenticator(
    config: EntraAuthConfig,
    *,
    document_fetcher: DocumentFetcher = fetch_json_document,
) -> EntraAuthenticator:
    """Compose trusted discovery, cached JWKS, JWT verification and role mapping.

    The discovery URL is fixed in config. Discovery's issuer must exactly match
    expected_issuer, and its JWKS hostname must be in allowed_jwks_hosts.
    document_fetcher is injectable for tests; production should use the default
    bounded HTTPS transport.
    """
    if not callable(document_fetcher):
        raise ValueError("document_fetcher must be callable")

    def fetch_document(url: str, allowed_hosts: frozenset[str]) -> dict[str, Any]:
        return fetch_trusted_document(
            url,
            trusted_hosts=set(allowed_hosts),
            timeout_seconds=config.timeout_seconds,
            transport=lambda requested_url, timeout: document_fetcher(
                requested_url,
                trusted_hosts=set(allowed_hosts),
                timeout_seconds=timeout,
                max_response_bytes=config.max_response_bytes,
            ),
        )

    discovery = fetch_document(
        config.discovery_url, config.trusted_metadata_hosts
    )
    metadata = validate_discovery_document(
        discovery,
        expected_issuer=config.expected_issuer,
        allowed_jwks_hosts=set(config.allowed_jwks_hosts),
    )

    def load_jwks() -> dict[str, Any]:
        return fetch_document(metadata.jwks_uri, config.allowed_jwks_hosts)

    cache = JWKSCache(load_jwks, ttl_seconds=config.jwks_ttl_seconds)
    return EntraAuthenticator(config, metadata, cache)