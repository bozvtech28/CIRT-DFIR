import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from case_repository import (
    connect, create_case, get_case, initialize, list_audit_events, list_cases, update_case
)

BASE = Path(__file__).resolve().parent
SCHEMA = BASE / "phase6_schema.sql"


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "synthetic-test.sqlite"
        initialize(self.database, SCHEMA)
        self.db = connect(self.database)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def make_case(self, case_id="DEMO-REPO-001"):
        return create_case(
            self.db,
            case_id=case_id,
            title="Synthetic repository test",
            severity="High",
            status="Investigating",
            actor_id="synthetic-test",
            timestamp="2026-01-01T00:00:00Z",
        )

    def test_create_and_retrieve_case(self):
        case = self.make_case()
        self.assertEqual(case["case_id"], "DEMO-REPO-001")
        self.assertEqual(get_case(self.db, "DEMO-REPO-001")["severity"], "High")

    def test_list_cases(self):
        self.make_case("DEMO-REPO-002")
        self.make_case("DEMO-REPO-001")
        self.assertEqual(
            [c["case_id"] for c in list_cases(self.db)],
            ["DEMO-REPO-001", "DEMO-REPO-002"],
        )

    def test_missing_case_returns_none(self):
        self.assertIsNone(get_case(self.db, "DEMO-MISSING"))

    def test_creation_records_audit_event(self):
        self.make_case()
        events = list_audit_events(self.db, "DEMO-REPO-001")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "CASE_CREATED")
        self.assertEqual(events[0]["actor_id"], "synthetic-test")
        self.assertTrue(json.loads(events[0]["details_json"])["synthetic"])

    def test_invalid_severity_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            create_case(
                self.db,
                case_id="DEMO-INVALID",
                title="Synthetic invalid test",
                severity="Extreme",
                status="Triage",
                actor_id="synthetic-test",
                timestamp="2026-01-01T00:00:00Z",
            )

    def test_empty_actor_is_rejected(self):
        with self.assertRaises(ValueError):
            create_case(
                self.db,
                case_id="DEMO-EMPTY-ACTOR",
                title="Synthetic test",
                severity="Low",
                status="Triage",
                actor_id="",
                timestamp="2026-01-01T00:00:00Z",
            )

    def test_duplicate_case_id_is_rejected(self):
        self.make_case()
        with self.assertRaises(sqlite3.IntegrityError):
            self.make_case()

    def test_audit_event_cannot_be_updated(self):
        self.make_case()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE audit_events SET event_type='ALTERED' WHERE event_id=1"
            )

    def test_audit_event_cannot_be_deleted(self):
        self.make_case()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM audit_events WHERE event_id=1")


if __name__ == "__main__":
    unittest.main(verbosity=2)


    def test_update_case_records_before_and_after_audit(self):
        import json
        self.make_case()
        updated = update_case(
            self.db,
            case_id="DEMO-REPO-001",
            actor_id="synthetic-reviewer",
            timestamp="2026-10-15T12:00:00Z",
            status="Investigating",
            severity="High",
        )
        self.assertEqual(updated["status"], "Investigating")
        self.assertEqual(updated["severity"], "High")
        events = list_audit_events(self.db, "DEMO-REPO-001")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1]["event_type"], "CASE_UPDATED")
        details = json.loads(events[-1]["details_json"])
        self.assertTrue(details["synthetic"])
        self.assertEqual(details["before"]["status"], "Triage")
        self.assertEqual(details["after"]["status"], "Investigating")


    def test_update_missing_case_returns_none(self):
        result = update_case(
            self.db,
            case_id="DEMO-MISSING",
            actor_id="synthetic-reviewer",
            timestamp="2026-10-15T12:00:00Z",
            status="Investigating",
        )
        self.assertIsNone(result)


    def test_update_rejects_invalid_status(self):
        self.make_case()
        with self.assertRaises(ValueError):
            update_case(
                self.db,
                case_id="DEMO-REPO-001",
                actor_id="synthetic-reviewer",
                timestamp="2026-10-15T12:00:00Z",
                status="Unknown",
            )


    def test_update_rejects_empty_actor(self):
        self.make_case()
        with self.assertRaises(ValueError):
            update_case(
                self.db,
                case_id="DEMO-REPO-001",
                actor_id=" ",
                timestamp="2026-10-15T12:00:00Z",
                status="Investigating",
            )


    def test_update_rejects_no_change(self):
        self.make_case()
        with self.assertRaises(ValueError):
            update_case(
                self.db,
                case_id="DEMO-REPO-001",
                actor_id="synthetic-reviewer",
                timestamp="2026-10-15T12:00:00Z",
                status="Triage",
            )


