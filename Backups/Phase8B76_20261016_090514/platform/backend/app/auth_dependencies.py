"""Fail-closed authentication gate pending approved OIDC integration.

This module intentionally authenticates nobody. Replace the placeholder
identity provider integration only after the organization chooses a provider.
Never trust roles supplied by a browser or request body.
"""
from fastapi import Depends, HTTPException

from app.security import (
    AuthenticationRequired,
    AuthorizationDenied,
    Principal,
    authorize,
)

def get_current_principal() -> Principal:
    """Reject all requests until real token/session validation is implemented."""
    raise HTTPException(
        status_code=401,
        detail="Authentication is not configured. Access is denied by default.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_permission(permission: str):
    """Require a validated principal and enforce the RBAC permission."""
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        try:
            authorize(principal, permission)
        except AuthenticationRequired as exc:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except AuthorizationDenied as exc:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permission.",
            ) from exc
        return principal
    return dependency
