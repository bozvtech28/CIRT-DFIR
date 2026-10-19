"""RBAC policy foundation for CIRT DFIR Professional.

This module authorizes an already authenticated principal.
It does not authenticate users or validate OIDC tokens.
Do not treat a caller-created Principal as proof of identity.
"""

from dataclasses import dataclass
from typing import FrozenSet


ROLE_ADMINISTRATOR = "Administrator"
ROLE_ANALYST = "DFIR Analyst"
ROLE_VIEWER = "Viewer"

KNOWN_ROLES: FrozenSet[str] = frozenset({
    ROLE_ADMINISTRATOR,
    ROLE_ANALYST,
    ROLE_VIEWER,
})

PERMISSIONS = {
    "cases:read": frozenset({
        ROLE_ADMINISTRATOR,
        ROLE_ANALYST,
        ROLE_VIEWER,
    }),
    "cases:update": frozenset({
        ROLE_ADMINISTRATOR,
        ROLE_ANALYST,
    }),
    "users:manage": frozenset({
        ROLE_ADMINISTRATOR,
    }),
    "audit:read": frozenset({
        ROLE_ADMINISTRATOR,
    }),
}


@dataclass(frozen=True)
class Principal:
    """Identity and roles supplied by a trusted authentication layer."""
    subject: str
    roles: FrozenSet[str]


class AuthenticationRequired(PermissionError):
    """Raised when no authenticated principal is available."""


class AuthorizationDenied(PermissionError):
    """Raised when the principal lacks the required permission."""


def validate_principal(principal: Principal | None) -> Principal:
    if principal is None:
        raise AuthenticationRequired("Authentication is required.")
    if not isinstance(principal, Principal):
        raise AuthenticationRequired("A trusted principal is required.")
    if not isinstance(principal.subject, str) or not principal.subject.strip():
        raise AuthenticationRequired("Principal subject is missing.")
    if not principal.roles:
        raise AuthorizationDenied("Principal has no assigned roles.")
    if not principal.roles.issubset(KNOWN_ROLES):
        raise AuthorizationDenied("Principal contains an unknown role.")
    return principal


def authorize(principal: Principal | None, permission: str) -> bool:
    """Authorize a trusted principal for a named permission.

    The caller must obtain the principal from a verified authentication
    mechanism, such as validated OIDC claims. Never build it from request
    fields supplied by the client.
    """
    trusted = validate_principal(principal)
    allowed_roles = PERMISSIONS.get(permission)
    if allowed_roles is None:
        raise AuthorizationDenied("Unknown permission.")
    if trusted.roles.isdisjoint(allowed_roles):
        raise AuthorizationDenied("Permission denied.")
    return True
