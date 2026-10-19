import sys
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

backend = Path(sys.argv[1])
app_dir = backend / "app"
sys.path.insert(0, str(backend))

from app import case_store
from app.main import app

class Phase7DTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cirt_phase7d_")
        self.old_db_path = case_store.DB_PATH
        case_store.DB_PATH = Path(self.temp.name) / "synthetic_test.sqlite"
        self.client = TestClient(app)
        case_store.ensure_database()

    def tearDown(self):
        self.client.close()
        case_store.DB_PATH = self.old_db_path
        self.temp.cleanup()

    def test_health_remains_available(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_demo_case_update_and_audit(self):
        response = self.client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"status": "Evidence review", "severity": "Critical"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["status"], "Evidence review")
        self.assertEqual(data["severity"], "Critical")

        db = case_store.connect(case_store.DB_PATH)
        try:
            events = db.execute(
                """SELECT event_type, actor_id, details_json
                   FROM audit_events
                   WHERE case_id = ?
                   ORDER BY event_id""",
                ("DEMO-2026-001",),
            ).fetchall()
        finally:
            db.close()

        self.assertTrue(any(row["event_type"] == "CASE_UPDATED" for row in events))
        update_event = [row for row in events if row["event_type"] == "CASE_UPDATED"][-1]
        self.assertEqual(update_event["actor_id"], "DEVELOPMENT-API")
        self.assertIn('"before"', update_event["details_json"])
        self.assertIn('"after"', update_event["details_json"])

    def test_invalid_status_is_rejected(self):
        response = self.client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"status": "Arbitrary status"},
        )
        self.assertEqual(response.status_code, 422)

    def test_unknown_fields_are_rejected(self):
        response = self.client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"title": "Unexpected edit"},
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_case_returns_404(self):
        response = self.client.patch(
            "/api/v1/cases/DEMO-DOES-NOT-EXIST",
            json={"status": "Closed"},
        )
        self.assertEqual(response.status_code, 404)

    def test_no_change_returns_conflict(self):
        response = self.client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"status": "Investigating", "severity": "High"},
        )
        self.assertEqual(response.status_code, 409)

    def test_empty_update_is_rejected(self):
        response = self.client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={},
        )
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Phase7DTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"PHASE7D_SUMMARY ran={result.testsRun}; "
        f"failures={len(result.failures)}; errors={len(result.errors)}"
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)