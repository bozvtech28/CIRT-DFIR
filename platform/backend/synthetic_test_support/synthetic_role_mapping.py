"""Synthetic role mapping for offline tests only.

This module is deliberately isolated from production application code.
It accepts role labels only; it does not authenticate tokens or prove
that claims came from a trusted identity provider.
"""

from collections.abc import Iterable

# Provisional examples for testing only.
# These values are not approved Microsoft Entra app-role identifiers.
_SYNTHETIC_ROLE_PERMISSIONS = {
    "Viewer": frozenset({"cases:read"}),
    "Analyst": frozenset({"cases:read", "cases:update"}),
    "Admin": frozenset({
        "cases:read",
        "cases:update",
        "users:manage",
        "audit:read",
    }),
}


def map_synthetic_roles_to_permissions(
    roles: Iterable[str],
) -> frozenset[str]:
    """Map exact synthetic role labels to permissions.

    Unknown roles and malformed inputs fail closed. This helper must
    only be used with synthetic test data and must never be treated as
    proof that a token or identity has been authenticated.
    """
    if isinstance(roles, (str, bytes)):
        raise ValueError("Roles must be an iterable of role labels, not a string.")

    try:
        role_list = list(roles)
    except TypeError as exc:
        raise ValueError("Roles must be an iterable of role labels.") from exc

    if not role_list:
        raise ValueError("At least one role is required.")

    if any(not isinstance(role, str) or not role.strip() for role in role_list):
        raise ValueError("Every role must be a non-empty string.")

    unknown = sorted(set(role_list) - set(_SYNTHETIC_ROLE_PERMISSIONS))
    if unknown:
        raise ValueError("Unknown synthetic role(s): " + ", ".join(unknown))

    permissions = set()
    for role in role_list:
        permissions.update(_SYNTHETIC_ROLE_PERMISSIONS[role])

    return frozenset(permissions)
