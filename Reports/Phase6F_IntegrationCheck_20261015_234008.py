import os
import sys
import tempfile
import traceback
from pathlib import Path

BACKEND = Path(r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend")
TESTS = BACKEND / "tests"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(TESTS))

failures = []
passed = []

def check(name, func):
    try:
        detail = func()
        passed.append(name)
        print(f"PASS: {name}: {detail}")
    except Exception as exc:
        failures.append(name)
        print(f"FAIL: {name}: {type(exc).__name__}: {exc}")
        traceback.print_exc()

with tempfile.TemporaryDirectory(prefix="cirt_phase6f_") as temp:
    os.environ["CIRT_DFIR_DB_PATH"] = str(Path(temp) / "integration.sqlite")

    def api_health():
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload.get("status") == "ok", payload
            assert payload.get("mode") == "development-scaffold", payload
            return f"HTTP {response.status_code}; development scaffold"

    def api_demo_cases():
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            response = client.get("/api/v1/demo/cases")
            assert response.status_code == 200, response.text
            data = response.json()
            assert len(data) == 3, data
            assert all(item["case_id"].startswith("DEMO-") for item in data), data
            assert all(item["severity"] in ("Low", "Medium", "High", "Critical") for item in data), data
            return f"HTTP {response.status_code}; {len(data)} synthetic cases"

    def repository_audit_consistency():
        from app.case_store import list_demo_cases
        from app.case_repository import connect
        from app.case_store import DB_PATH
        cases = list_demo_cases()
        assert len(cases) == 3, cases
        db = connect(DB_PATH)
        try:
            count = db.execute(
                "SELECT COUNT(*) FROM audit_events WHERE case_id LIKE 'DEMO-%'"
            ).fetchone()[0]
            assert count == 3, f"Expected three demo audit events, got {count}"
            return f"{len(cases)} demo cases and {count} corresponding creation audit events"
        finally:
            db.close()

    def schema_trigger_check():
        from app.case_store import DB_PATH
        from app.case_repository import connect
        db = connect(DB_PATH)
        try:
            rows = db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                "AND name IN ('audit_events_no_update', 'audit_events_no_delete')"
            ).fetchall()
            names = {row["name"] for row in rows}
            expected = {"audit_events_no_update", "audit_events_no_delete"}
            assert names == expected, f"Expected {expected}, got {names}"
            return "Both audit update/delete protection triggers exist"
        finally:
            db.close()

    def api_source_contract():
        source = (BACKEND / "app" / "main.py").read_text(encoding="utf-8")
        assert "from app.case_store import list_demo_cases" in source
        assert "return [DemoCase(**item) for item in list_demo_cases()]" in source
        return "Demo-case endpoint is wired to the repository-backed store"

    import unittest

    def repository_unit_tests():
        import importlib.util
        test_path = Path(r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\database-design\\test_case_repository.py")
        spec = importlib.util.spec_from_file_location("phase6f_repository_tests", test_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = unittest.TestResult()
        suite.run(result)
        if not result.wasSuccessful():
            raise AssertionError(
                f"Ran {result.testsRun}; failures={len(result.failures)}; "
                f"errors={len(result.errors)}; details={result.failures + result.errors}"
            )
        return f"{result.testsRun} tests passed"

    check("API health contract", api_health)
    check("Synthetic demo-case endpoint", api_demo_cases)
    check("Repository and audit-event consistency", repository_audit_consistency)
    check("Audit protection triggers", schema_trigger_check)
    check("API repository wiring", api_source_contract)
    check("Repository unit tests", repository_unit_tests)

    os.environ.pop("CIRT_DFIR_DB_PATH", None)

print(f"\nPhase 6F Python checks: {len(passed)} passed, {len(failures)} failed")
for name in failures:
    print(f"FAILED CHECK: {name}")
sys.exit(1 if failures else 0)