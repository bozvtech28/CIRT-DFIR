import unittest

from app.entra_config_preflight import validate_entra_config


class EntraConfigPreflightTests(unittest.TestCase):
    def valid_config(self):
        return {
            "tenant_id": "11111111-2222-4333-8444-555555555555",
            "expected_issuer": "https://login.microsoftonline.com/example-tenant/v2.0",
            "expected_audience": "api://example-api",
            "approved_role_map": {
                "Example.Viewer": "Viewer",
                "Example.Analyst": "DFIR Analyst",
                "Example.Administrator": "Administrator",
            },
        }

    def test_valid_structure_returns_no_errors(self):
        self.assertEqual(validate_entra_config(self.valid_config()), [])

    def test_missing_tenant_is_rejected(self):
        config = self.valid_config()
        del config["tenant_id"]
        self.assertTrue(any("tenant_id is required" in e for e in validate_entra_config(config)))

    def test_invalid_tenant_uuid_is_rejected(self):
        config = self.valid_config()
        config["tenant_id"] = "not-a-uuid"
        self.assertTrue(any("valid UUID" in e for e in validate_entra_config(config)))

    def test_http_issuer_is_rejected(self):
        config = self.valid_config()
        config["expected_issuer"] = "http://login.example.test/tenant"
        self.assertTrue(any("fixed HTTPS URL" in e for e in validate_entra_config(config)))

    def test_issuer_credentials_are_rejected(self):
        config = self.valid_config()
        config["expected_issuer"] = "https://user:pass@login.example.test/tenant"
        self.assertTrue(any("fixed HTTPS URL" in e for e in validate_entra_config(config)))

    def test_issuer_query_is_rejected(self):
        config = self.valid_config()
        config["expected_issuer"] = "https://login.example.test/tenant?x=1"
        self.assertTrue(any("fixed HTTPS URL" in e for e in validate_entra_config(config)))

    def test_empty_audience_is_rejected(self):
        config = self.valid_config()
        config["expected_audience"] = " "
        self.assertTrue(any("expected_audience" in e for e in validate_entra_config(config)))

    def test_empty_role_map_is_rejected(self):
        config = self.valid_config()
        config["approved_role_map"] = {}
        self.assertTrue(any("non-empty mapping" in e for e in validate_entra_config(config)))

    def test_unapproved_internal_role_is_rejected(self):
        config = self.valid_config()
        config["approved_role_map"] = {"Example.Root": "Superuser"}
        self.assertTrue(any("not an approved internal role" in e for e in validate_entra_config(config)))

    def test_non_mapping_input_is_rejected(self):
        self.assertTrue(validate_entra_config(None))


if __name__ == "__main__":
    unittest.main()
