import pytest

from app.security import authorize, AuthorizationDenied
from app.entra_principal import principal_from_verified_claims


TEST_ROLE_MAP = {
    "CIRT.DFIR.Viewer": "Viewer",
    "CIRT.DFIR.Analyst": "DFIR Analyst",
    "CIRT.DFIR.Administrator": "Administrator",
}


def make_principal(app_role):
    return principal_from_verified_claims(
        {
            "sub": "synthetic-authorization-test-user",
            "roles": [app_role],
        },
        approved_role_map=TEST_ROLE_MAP,
    )


def test_viewer_can_read_cases():
    principal = make_principal("CIRT.DFIR.Viewer")
    authorize(principal, "cases:read")


def test_viewer_cannot_update_cases():
    principal = make_principal("CIRT.DFIR.Viewer")
    with pytest.raises(AuthorizationDenied):
        authorize(principal, "cases:update")


def test_analyst_can_read_cases():
    principal = make_principal("CIRT.DFIR.Analyst")
    authorize(principal, "cases:read")


def test_analyst_can_update_cases():
    principal = make_principal("CIRT.DFIR.Analyst")
    authorize(principal, "cases:update")


def test_analyst_cannot_manage_users():
    principal = make_principal("CIRT.DFIR.Analyst")
    with pytest.raises(AuthorizationDenied):
        authorize(principal, "users:manage")


def test_administrator_can_read_cases():
    principal = make_principal("CIRT.DFIR.Administrator")
    authorize(principal, "cases:read")


def test_administrator_can_update_cases():
    principal = make_principal("CIRT.DFIR.Administrator")
    authorize(principal, "cases:update")


def test_administrator_can_manage_users():
    principal = make_principal("CIRT.DFIR.Administrator")
    authorize(principal, "users:manage")


def test_administrator_can_read_audit():
    principal = make_principal("CIRT.DFIR.Administrator")
    authorize(principal, "audit:read")


def test_unknown_permission_is_denied():
    principal = make_principal("CIRT.DFIR.Administrator")
    with pytest.raises(AuthorizationDenied):
        authorize(principal, "system:unapproved")
