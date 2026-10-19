"""Offline preflight validation for Microsoft Entra configuration.

This module does not read or modify process environment variables, perform
network requests, or enable authentication.
"""
from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlparse
from uuid import UUID


REQUIRED_KEYS = (
    "tenant_id",
    "expected_issuer",
    "expected_audience",
    "approved_role_map",
)


def validate_entra_config(config: Mapping[str, object]) -> list[str]:
    """Return validation errors. An empty list means structurally valid only."""
    errors: list[str] = []

    if not isinstance(config, Mapping):
        return ["config must be a mapping"]

    for key in REQUIRED_KEYS:
        if key not in config:
            errors.append(f"{key} is required")

    tenant_id = config.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        errors.append("tenant_id must be a non-empty string")
    else:
        try:
            UUID(tenant_id)
        except (ValueError, AttributeError, TypeError):
            errors.append("tenant_id must be a valid UUID")

    issuer = config.get("expected_issuer")
    if not isinstance(issuer, str) or not issuer.strip():
        errors.append("expected_issuer must be a non-empty string")
    else:
        try:
            parsed = urlparse(issuer)
            valid_issuer = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and parsed.port in (None, 443)
                and not parsed.query
                and not parsed.fragment
                and not parsed.params
            )
        except ValueError:
            valid_issuer = False
        if not valid_issuer:
            errors.append(
                "expected_issuer must be a fixed HTTPS URL without credentials, "
                "query, fragment, or a nonstandard port"
            )

    audience = config.get("expected_audience")
    if not isinstance(audience, str) or not audience.strip():
        errors.append("expected_audience must be a non-empty string")

    role_map = config.get("approved_role_map")
    if not isinstance(role_map, Mapping) or not role_map:
        errors.append("approved_role_map must be a non-empty mapping")
    else:
        allowed_internal_roles = {"Administrator", "DFIR Analyst", "Viewer"}
        seen_values: set[str] = set()

        for external_role, internal_role in role_map.items():
            if not isinstance(external_role, str) or not external_role.strip():
                errors.append("external role names must be non-empty strings")
                continue
            if external_role in seen_values:
                errors.append("duplicate external role value")
            seen_values.add(external_role)

            if not isinstance(internal_role, str) or internal_role not in allowed_internal_roles:
                errors.append(
                    f"internal role for {external_role!r} is not an approved internal role"
                )

    return errors
