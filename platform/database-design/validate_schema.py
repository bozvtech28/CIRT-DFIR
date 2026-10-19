import json
import sqlite3
import sys

schema_path = sys.argv[1]
with open(schema_path, "r", encoding="utf-8") as stream:
    schema = stream.read()

checks = []

def record(name, passed, detail):
    checks.append((name, bool(passed), detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")

try:
    # In-memory database only: no persistent case database is created.
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(schema)

    tables = {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    record(
        "Required tables",
        {"cases", "audit_events"}.issubset(tables),
        f"Found {sorted(tables)}",
    )

    indexes = {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
    }
    record(
        "Lookup indexes",
        {"idx_cases_status", "idx_cases_severity", "idx_audit_case_time"}.issubset(indexes),
        f"Found expected indexes: {sorted(indexes)}",
    )

    now = "2026-01-01T00:00:00Z"
    db.execute(
        """INSERT INTO cases
           (case_id, title, severity, status, created_at, updated_at, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("DEMO-TEST-001", "Synthetic schema validation", "High",
         "Investigating", now, now, "synthetic-test"),
    )
    db.execute(
        """INSERT INTO audit_events
           (case_id, event_type, actor_id, event_time, details_json)
           VALUES (?, ?, ?, ?, ?)""",
        ("DEMO-TEST-001", "CASE_CREATED", "synthetic-test", now,
         json.dumps({"synthetic": True, "purpose": "schema-validation"})),
    )
    db.commit()

    case_count = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    event_count = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    record(
        "Synthetic insert and relationship",
        case_count == 1 and event_count == 1,
        f"cases={case_count}; audit_events={event_count}",
    )

    try:
        db.execute(
            "UPDATE audit_events SET event_type='CHANGED' WHERE event_id=1"
        )
        update_blocked = False
    except sqlite3.IntegrityError:
        update_blocked = True
    record(
        "Audit update protection",
        update_blocked,
        "Update was rejected by append-only trigger" if update_blocked
        else "Unexpectedly allowed an audit-event update",
    )

    try:
        db.execute("DELETE FROM audit_events WHERE event_id=1")
        delete_blocked = False
    except sqlite3.IntegrityError:
        delete_blocked = True
    record(
        "Audit delete protection",
        delete_blocked,
        "Delete was rejected by append-only trigger" if delete_blocked
        else "Unexpectedly allowed an audit-event deletion",
    )

    try:
        db.execute(
            """INSERT INTO cases
               (case_id, title, severity, status, created_at, updated_at, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("DEMO-TEST-BAD", "Invalid severity", "Extreme", "Triage",
             now, now, "synthetic-test"),
        )
        invalid_severity_blocked = False
    except sqlite3.IntegrityError:
        invalid_severity_blocked = True
    record(
        "Severity constraint",
        invalid_severity_blocked,
        "Invalid severity rejected" if invalid_severity_blocked
        else "Invalid severity was unexpectedly accepted",
    )

    db.close()
except Exception as exc:
    record("Schema execution", False, f"{type(exc).__name__}: {exc}")

failed = [item for item in checks if not item[1]]
print()
print(f"Checks passed: {len(checks) - len(failed)}/{len(checks)}")
print("Database mode: in-memory SQLite; no persistent database created.")
sys.exit(1 if failed else 0)