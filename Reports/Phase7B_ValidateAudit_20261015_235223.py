import json
import sqlite3
import sys
import tempfile
from pathlib import Path

design_dir = Path(sys.argv[1])
repository_path = Path(sys.argv[2])
schema_path = Path(sys.argv[3])

sys.path.insert(0, str(design_dir))

from case_repository import (
    connect,
    initialize,
    create_case,
    get_case,
    list_audit_events,
    update_case,
)

passed = 0
failed = 0

def check(name, function):
    global passed, failed
    try:
        detail = function()
        passed += 1
        print(f"PASS | {name}" + (f" | {detail}" if detail else ""))
    except Exception as exc:
        failed += 1
        print(f"FAIL | {name} | {type(exc).__name__}: {exc}")

def new_database(folder, label):
    path = Path(folder) / f"{label}.sqlite"
    initialize(path, schema_path)
    db = connect(path)
    create_case(
        db,
        case_id="DEMO-7B-001",
        title="Synthetic audit validation",
        severity="High",
        status="Investigating",
        actor_id="SYNTHETIC-TEST",
        timestamp="2026-10-15T12:00:00Z",
    )
    return path, db

with tempfile.TemporaryDirectory(prefix="cirt_phase7b_") as temp:
    # Check 1: Confirm the fixture starts with expected synthetic values.
    state = {}
    def check_initial_case():
        path, db = new_database(temp, "normal")
        state["path"] = path
        state["db"] = db
        case = get_case(db, "DEMO-7B-001")
        assert case is not None, "Synthetic case was not created"
        assert case["status"] == "Investigating", case
        assert case["severity"] == "High", case
        return "Initial status=Investigating; severity=High"
    check("Synthetic fixture initialization", check_initial_case)

    # Check 2: Verify an update changes the requested fields.
    def check_update_fields():
        db = state["db"]
        updated = update_case(
            db,
            case_id="DEMO-7B-001",
            actor_id="SYNTHETIC-REVIEWER",
            timestamp="2026-10-15T12:05:00Z",
            status="Evidence review",
            severity="Critical",
        )
        assert updated["status"] == "Evidence review", updated
        assert updated["severity"] == "Critical", updated
        assert updated["updated_at"] == "2026-10-15T12:05:00Z", updated
        return "Status, severity, and updated_at verified"
    check("Case update fields", check_update_fields)

    # Check 3: Confirm the audit event records before/after values.
    def check_audit_before_after():
        db = state["db"]
        events = list_audit_events(db, "DEMO-7B-001")
        updates = [event for event in events if event["event_type"] == "CASE_UPDATED"]
        assert len(updates) == 1, f"Expected 1 CASE_UPDATED event; got {len(updates)}"
        event = updates[0]
        details = json.loads(event["details_json"])
        assert details.get("synthetic") is True, details
        assert details["before"]["status"] == "Investigating", details
        assert details["before"]["severity"] == "High", details
        assert details["after"]["status"] == "Evidence review", details
        assert details["after"]["severity"] == "Critical", details
        assert event["actor_id"] == "SYNTHETIC-REVIEWER", event
        return "Exactly one update event; actor and before/after values verified"
    check("Audit event before/after integrity", check_audit_before_after)

    # Check 4: Invalid status must not alter the case or add an audit event.
    def check_invalid_update():
        db = state["db"]
        before = get_case(db, "DEMO-7B-001")
        audit_count = len(list_audit_events(db, "DEMO-7B-001"))
        try:
            update_case(
                db,
                case_id="DEMO-7B-001",
                actor_id="SYNTHETIC-REVIEWER",
                timestamp="2026-10-15T12:06:00Z",
                status="NOT-A-VALID-STATUS",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid status was accepted")
        after = get_case(db, "DEMO-7B-001")
        assert dict(after) == dict(before), "Case changed after rejected update"
        assert len(list_audit_events(db, "DEMO-7B-001")) == audit_count, "Audit count changed"
        return "Rejected update left case and audit history unchanged"
    check("Invalid update is non-mutating", check_invalid_update)

    # Check 5: No-change updates should be rejected.
    def check_no_change():
        db = state["db"]
        before = get_case(db, "DEMO-7B-001")
        audit_count = len(list_audit_events(db, "DEMO-7B-001"))
        try:
            update_case(
                db,
                case_id="DEMO-7B-001",
                actor_id="SYNTHETIC-REVIEWER",
                timestamp="2026-10-15T12:07:00Z",
                status=before["status"],
                severity=before["severity"],
            )
        except ValueError:
            pass
        else:
            raise AssertionError("No-change update was accepted")
        assert dict(get_case(db, "DEMO-7B-001")) == dict(before)
        assert len(list_audit_events(db, "DEMO-7B-001")) == audit_count
        return "No-change update rejected without mutation"
    check("No-change update is rejected", check_no_change)

    # Close the normal test database before the rollback scenario.
    if "db" in state:
        state["db"].close()

    # Check 6: A failed audit insert must roll back the case update.
    def check_audit_failure_rollback():
        path, db = new_database(temp, "rollback")
        try:
            before = get_case(db, "DEMO-7B-001")
            audit_count = len(list_audit_events(db, "DEMO-7B-001"))

            db.execute("""
                CREATE TRIGGER reject_synthetic_case_update_audit
                BEFORE INSERT ON audit_events
                WHEN NEW.event_type = 'CASE_UPDATED'
                BEGIN
                    SELECT RAISE(ABORT, 'Synthetic audit failure test');
                END
            """)

            try:
                update_case(
                    db,
                    case_id="DEMO-7B-001",
                    actor_id="SYNTHETIC-REVIEWER",
                    timestamp="2026-10-15T12:08:00Z",
                    status="Contained",
                    severity="Critical",
                )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("Expected synthetic audit insert failure")

            after = get_case(db, "DEMO-7B-001")
            assert dict(after) == dict(before), (
                f"Case was not rolled back: before={dict(before)}, after={dict(after)}"
            )
            assert len(list_audit_events(db, "DEMO-7B-001")) == audit_count, (
                "Audit history changed after failed update"
            )
            return "Failed audit insert rolled back case changes"
        finally:
            db.close()
    check("Audit failure rollback", check_audit_failure_rollback)

    if "db" in state and state["db"]:
        try:
            state["db"].close()
        except Exception:
            pass

print()
print(f"SUMMARY | Passed={passed} | Failed={failed} | Total={passed + failed}")
print("SCOPE | Temporary SQLite databases and synthetic case data only")
print("SCOPE | No server started; no production collector or real evidence accessed")

if failed:
    raise SystemExit(1)