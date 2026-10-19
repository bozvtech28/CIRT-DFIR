import sys
import sqlite3
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\database-design")

from case_repository import (
    connect,
    initialize,
    create_case,
    get_case,
    list_cases,
)

SCHEMA = Path(r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\database-design\\phase6_schema.sql")
results = []

def check(name, function):
    try:
        detail = function()
        results.append((name, True, str(detail or "OK")))
        print(f"PASS: {name} - {detail or 'OK'}")
    except Exception as exc:
        results.append((name, False, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL: {name} - {type(exc).__name__}: {exc}")
        traceback.print_exc()

def run():
    with tempfile.TemporaryDirectory(prefix="cirt_phase6e_") as temp:
        database = Path(temp) / "phase6e_synthetic.sqlite"
        timestamp = "2026-10-15T00:00:00Z"

        def initialize_db():
            initialize(database, SCHEMA)
            assert database.exists() and database.stat().st_size > 0
            return "Temporary SQLite database initialized"

        check("Temporary database initialization", initialize_db)

        def create_and_retrieve():
            db = connect(database)
            try:
                create_case(
                    db,
                    case_id="TEST-6E-001",
                    title="Synthetic Endpoint Review",
                    severity="High",
                    status="Investigating",
                    actor_id="TEST-6E",
                    timestamp=timestamp,
                )
                case = get_case(db, "TEST-6E-001")
                assert case is not None, "Created case could not be retrieved"
                assert case["case_id"] == "TEST-6E-001"
                assert case["title"] == "Synthetic Endpoint Review"
                return "Created and retrieved the synthetic case"
            finally:
                db.close()

        check("Case creation and retrieval", create_and_retrieve)

        def duplicate_rejected():
            db = connect(database)
            try:
                try:
                    create_case(
                        db,
                        case_id="TEST-6E-001",
                        title="Duplicate Synthetic Case",
                        severity="Medium",
                        status="Triage",
                        actor_id="TEST-6E",
                        timestamp=timestamp,
                    )
                except (sqlite3.IntegrityError, ValueError):
                    db.rollback()
                    return "Duplicate case ID was rejected"
                raise AssertionError("Duplicate case ID was accepted")
            finally:
                db.close()

        check("Duplicate case ID rejection", duplicate_rejected)

        def case_list_count():
            db = connect(database)
            try:
                cases = list_cases(db)
                matches = [c for c in cases if c["case_id"] == "TEST-6E-001"]
                assert len(matches) == 1, f"Expected one matching case; got {len(matches)}"
                return f"{len(cases)} total case(s), one matching test case"
            finally:
                db.close()

        check("Case listing and uniqueness", case_list_count)

        def audit_recorded():
            db = connect(database)
            try:
                row = db.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE case_id = ?",
                    ("TEST-6E-001",),
                ).fetchone()
                count = int(row[0])
                assert count == 1, f"Expected one creation audit event; got {count}"
                return "One audit event recorded for case creation"
            finally:
                db.close()

        check("Case creation audit event", audit_recorded)

        def audit_update_blocked():
            db = connect(database)
            try:
                try:
                    db.execute(
                        "UPDATE audit_events SET event_hash = event_hash "
                        "WHERE rowid = (SELECT rowid FROM audit_events LIMIT 1)"
                    )
                    db.commit()
                except sqlite3.DatabaseError:
                    db.rollback()
                    return "Audit-event update blocked by database trigger"
                raise AssertionError("Audit-event update was not blocked")
            finally:
                db.close()

        check("Audit-event update protection", audit_update_blocked)

        def audit_delete_blocked():
            db = connect(database)
            try:
                try:
                    db.execute(
                        "DELETE FROM audit_events "
                        "WHERE rowid = (SELECT rowid FROM audit_events LIMIT 1)"
                    )
                    db.commit()
                except sqlite3.DatabaseError:
                    db.rollback()
                    return "Audit-event deletion blocked by database trigger"
                raise AssertionError("Audit-event deletion was not blocked")
            finally:
                db.close()

        check("Audit-event delete protection", audit_delete_blocked)

        def audit_still_present():
            db = connect(database)
            try:
                row = db.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE case_id = ?",
                    ("TEST-6E-001",),
                ).fetchone()
                assert int(row[0]) == 1, "Audit record count changed unexpectedly"
                return "Audit record remains after attempted update/delete"
            finally:
                db.close()

        check("Audit record retained", audit_still_present)

        def persistence_after_reopen():
            db = connect(database)
            db.close()
            db = connect(database)
            try:
                case = get_case(db, "TEST-6E-001")
                assert case is not None, "Case missing after reconnect"
                row = db.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE case_id = ?",
                    ("TEST-6E-001",),
                ).fetchone()
                assert int(row[0]) == 1, "Audit record missing after reconnect"
                return "Case and audit record persist after reconnect"
            finally:
                db.close()

        check("Persistence after reconnect", persistence_after_reopen)

        def initialization_idempotent():
            initialize(database, SCHEMA)
            db = connect(database)
            try:
                case_count = int(db.execute(
                    "SELECT COUNT(*) FROM cases WHERE case_id = ?",
                    ("TEST-6E-001",),
                ).fetchone()[0])
                audit_count = int(db.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE case_id = ?",
                    ("TEST-6E-001",),
                ).fetchone()[0])
                assert case_count == 1, f"Case count changed: {case_count}"
                assert audit_count == 1, f"Audit count changed: {audit_count}"
                return "Reinitialization did not duplicate case or audit records"
            finally:
                db.close()

        check("Repeated schema initialization", initialization_idempotent)

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print(f"\nPhase 6E checks: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1

sys.exit(run())