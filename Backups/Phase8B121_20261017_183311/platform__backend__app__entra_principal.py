"""Map verified Entra application-role claims to internal CIRT DFIR roles.

SECURITY BOUNDARY:
Only pass the claims returned by verify_entra_access_token after successful
cryptographic and issuer/audience/tenant validation. This module does not
validate token signatures or establish claim provenance.

approved_role_map must come from trusted server-side configuration. Never
accept it, the claims, or role assignments from browser-controlled input.
"""
from collections.abc import Mapping
from typing import Any

from app.security import KNOWN_ROLES, Principal


class PrincipalMappingError(ValueError):
    """Raised when verified claims cannot safely become an application principal."""


def principal_from_verified_claims(
    claims: Mapping[str, Any],
    *,
    approved_role_map: Mapping[str, str],
) -> Principal:
    """Create an internal Principal from verified claims and an explicit role map."""
    if not isinstance(claims, Mapping):
        raise PrincipalMappingError("Verified claims must be a mapping.")

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise PrincipalMappingError("A non-empty subject claim is required.")

    if not isinstance(approved_role_map, Mapping) or not approved_role_map:
        raise PrincipalMappingError("An explicit server-side role map is required.")

    for app_role, internal_role in approved_role_map.items():
        if not isinstance(app_role, str) or not app_role.strip():
            raise PrincipalMappingError("Role-map keys must be non-empty strings.")
        if not isinstance(internal_role, str) or internal_role not in KNOWN_ROLES:
            raise PrincipalMappingError("Role map contains an unrecognized internal role.")

    raw_roles = claims.get("roles")
    if not isinstance(raw_roles, list) or not raw_roles:
        raise PrincipalMappingError("A non-empty roles array is required.")

    if any(not isinstance(role, str) or not role.strip() for role in raw_roles):
        raise PrincipalMappingError("Every application role must be a non-empty string.")

    if len(set(raw_roles)) != len(raw_roles):
        raise PrincipalMappingError("Duplicate application roles are not accepted.")

    unknown_roles = [role for role in raw_roles if role not in approved_role_map]
    if unknown_roles:
        raise PrincipalMappingError("Claims contain an unapproved application role.")

    internal_roles = frozenset(approved_role_map[role] for role in raw_roles)
    if not internal_roles:
        raise PrincipalMappingError("No approved internal roles were resolved.")

    return Principal(subject=subject.strip(), roles=internal_roles)
