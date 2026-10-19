import os
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend")

checks = []

def check(name, action):
    try:
        action()
        checks.append((name, True, "PASS"))
        print(f"PASS: {name}")
    except Exception as exc:
        checks.append((name, False, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL: {name}: {type(exc).__name__}: {exc}")
        traceback.print_exc()

with tempfile.TemporaryDirectory(prefix="cirt_phase6c_validation_") as temp_dir:
    db_path = Path(temp_dir) / "synthetic_validation.sqlite"
    os.environ["CIRT_DFIR_DB_PATH"] = str(db_path)

    try:
        from fastapi.testclient import TestClient
        from app.main import app
        from app.case_store import ensure_database, list_demo_cases
        from app.case_repository import connect

        def database_initializes():
            ensure_database()
            assert db_path.exists(), "Database file was not created"

        def has_three_synthetic_cases():
            cases = list_demo_cases()
            assert len(cases) == 3, f"Expected 3 cases, got {len(cases)}"
            assert all(c["case_id"].startswith("DEMO-") for c in cases)
            assert {c["case_id"] for c in cases} == {
                "DEMO-2026-001",
                "DEMO-2026-002",
                "DEMO-2026-003",
            }

        def audit_events_created():
            db = connect(db_path)
            try:
                count = db.execute(
                    "SELECT COUNT(*) FROM audit_events"
                ).fetchone()[0]
                assert count == 3, f"Expected 3 creation audit events, got {count}"
            finally:
                db.close()

        def repeated_initialization_is_idempotent():
            ensure_database()
            ensure_database()
            db = connect(db_path)
            try:
                cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
                events = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
                assert cases == 3, f"Expected 3 cases after repeat, got {cases}"
                assert events == 3, f"Expected 3 audit events after repeat, got {events}"
            finally:
                db.close()

        def api_endpoints_work():
            with TestClient(app) as client:
                health = client.get("/api/v1/health")
                assert health.status_code == 200, health.text
                assert health.json()["status"] == "ok"

                response = client.get("/api/v1/demo/cases")
                assert response.status_code == 200, response.text
                cases = response.json()
                assert len(cases) == 3
                assert all(c["case_id"].startswith("DEMO-") for c in cases)

        check("SQLite database initializes", database_initializes)
        check("Exactly three synthetic cases are available", has_three_synthetic_cases)
        check("Three case-creation audit events exist", audit_events_created)
        check("Repeated initialization does not duplicate records", repeated_initialization_is_idempotent)
        check("Health and demo-case API endpoints return HTTP 200", api_endpoints_work)

    except Exception as exc:
        checks.append(("Validation setup/import", False, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL: Validation setup/import: {type(exc).__name__}: {exc}")
        traceback.print_exc()
    finally:
        os.environ.pop("CIRT_DFIR_DB_PATH", None)

failed = [item for item in checks if not item[1]]
print(f"\nChecks passed: {len(checks) - len(failed)}/{len(checks)}")
print(f"Checks failed: {len(failed)}")

for name, passed, detail in checks:
    if not passed:
        print(f"FAILED DETAIL: {name}: {detail}")

sys.exit(1 if failed or len(checks) != 5 else 0)