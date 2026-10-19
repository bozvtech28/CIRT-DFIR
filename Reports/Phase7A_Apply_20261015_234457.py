import sys
from pathlib import Path

repo_path = Path(sys.argv[1])
test_path = Path(sys.argv[2])

repo = repo_path.read_text(encoding="utf-8")
tests = test_path.read_text(encoding="utf-8")

if "def update_case(" in repo:
    raise SystemExit("STOP: update_case already exists; no changes made.")

anchor = "def get_case("
if repo.count(anchor) != 1:
    raise SystemExit("STOP: expected exactly one get_case() insertion point.")

function = '''

def update_case(
    db: sqlite3.Connection,
    *,
    case_id: str,
    actor_id: str,
    timestamp: str,
    status: str | None = None,
    severity: str | None = None,
) -> dict[str, Any] | None:
    """Update case status/severity and append an audit event atomically."""
    import json

    if not isinstance(actor_id, str) or not actor_id.strip():
        raise ValueError("actor_id must be a non-empty string.")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("timestamp must be a non-empty string.")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id must be a non-empty string.")

    allowed_statuses = {
        "Triage", "Investigating", "Evidence review", "Contained", "Closed"
    }
    allowed_severities = {"Low", "Medium", "High", "Critical"}

    if status is not None and status not in allowed_statuses:
        raise ValueError("Unsupported case status.")
    if severity is not None and severity not in allowed_severities:
        raise ValueError("Unsupported case severity.")
    if status is None and severity is None:
        raise ValueError("Provide status, severity, or both.")

    before_row = db.execute(
        """SELECT case_id, title, severity, status, created_at,
                  updated_at, created_by
           FROM cases WHERE case_id = ?""",
        (case_id,),
    ).fetchone()

    if before_row is None:
        return None

    before = dict(before_row)
    new_status = status if status is not None else before["status"]
    new_severity = severity if severity is not None else before["severity"]

    if new_status == before["status"] and new_severity == before["severity"]:
        raise ValueError("Update contains no case changes.")

    details = json.dumps(
        {
            "synthetic": True,
            "before": {
                "status": before["status"],
                "severity": before["severity"],
            },
            "after": {
                "status": new_status,
                "severity": new_severity,
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    try:
        db.execute(
            """UPDATE cases
               SET status = ?, severity = ?, updated_at = ?
               WHERE case_id = ?""",
            (new_status, new_severity, timestamp, case_id),
        )
        db.execute(
            """INSERT INTO audit_events
               (case_id, event_type, actor_id, event_time, details_json)
               VALUES (?, ?, ?, ?, ?)""",
            (case_id, "CASE_UPDATED", actor_id.strip(), timestamp, details),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    updated = db.execute(
        """SELECT case_id, title, severity, status, created_at,
                  updated_at, created_by
           FROM cases WHERE case_id = ?""",
        (case_id,),
    ).fetchone()
    return dict(updated) if updated is not None else None

'''

repo = repo.replace(anchor, function + "\n" + anchor, 1)

if "def update_case(" not in tests:
    import_line = "    connect, create_case, get_case, initialize, list_audit_events, list_cases"
    replacement = "    connect, create_case, get_case, initialize, list_audit_events, list_cases, update_case"
    if import_line not in tests:
        raise SystemExit("STOP: expected repository-test import line not found.")
    tests = tests.replace(import_line, replacement, 1)

    test_block = '''

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
'''
    tests = tests.rstrip() + "\n" + test_block + "\n"

repo_path.write_text(repo, encoding="utf-8", newline="\n")
test_path.write_text(tests, encoding="utf-8", newline="\n")
print("Patch applied to database-design workspace only.")