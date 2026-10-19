import unittest

from app.security import (
    AuthenticationRequired,
    AuthorizationDenied,
    Principal,
    ROLE_ADMINISTRATOR,
    ROLE_ANALYST,
    ROLE_VIEWER,
    authorize,
)


class TestRBACPolicy(unittest.TestCase):
    def setUp(self):
        self.admin = Principal("synthetic-admin", frozenset({ROLE_ADMINISTRATOR}))
        self.analyst = Principal("synthetic-analyst", frozenset({ROLE_ANALYST}))
        self.viewer = Principal("synthetic-viewer", frozenset({ROLE_VIEWER}))

    def test_admin_can_read_update_manage_users_and_read_audit(self):
        for permission in ("cases:read", "cases:update", "users:manage", "audit:read"):
            with self.subTest(permission=permission):
                self.assertTrue(authorize(self.admin, permission))

    def test_analyst_can_read_and_update_cases(self):
        self.assertTrue(authorize(self.analyst, "cases:read"))
        self.assertTrue(authorize(self.analyst, "cases:update"))

    def test_analyst_cannot_manage_users_or_read_audit(self):
        for permission in ("users:manage", "audit:read"):
            with self.subTest(permission=permission):
                with self.assertRaises(AuthorizationDenied):
                    authorize(self.analyst, permission)

    def test_viewer_can_read_cases(self):
        self.assertTrue(authorize(self.viewer, "cases:read"))

    def test_viewer_cannot_update_cases(self):
        with self.assertRaises(AuthorizationDenied):
            authorize(self.viewer, "cases:update")

    def test_missing_principal_is_rejected(self):
        with self.assertRaises(AuthenticationRequired):
            authorize(None, "cases:read")

    def test_unknown_role_is_rejected(self):
        principal = Principal("synthetic-user", frozenset({"SuperUser"}))
        with self.assertRaises(AuthorizationDenied):
            authorize(principal, "cases:read")

    def test_unknown_permission_is_rejected(self):
        with self.assertRaises(AuthorizationDenied):
            authorize(self.admin, "database:destroy")

    def test_empty_subject_is_rejected(self):
        principal = Principal(" ", frozenset({ROLE_ADMINISTRATOR}))
        with self.assertRaises(AuthenticationRequired):
            authorize(principal, "cases:read")

    def test_no_roles_is_rejected(self):
        principal = Principal("synthetic-user", frozenset())
        with self.assertRaises(AuthorizationDenied):
            authorize(principal, "cases:read")


if __name__ == "__main__":
    unittest.main()
