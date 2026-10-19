import os, sys, tempfile, traceback, unittest
from pathlib import Path

BACKEND = Path(r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend")
DESIGN = Path(r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\database-design")
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))
sys.path.insert(0, str(DESIGN))

passed = []
failed = []

def check(name, func):
    try:
        detail = func()
        passed.append(name)
        print(f"PASS: {name} - {detail}")
    except Exception as exc:
        failed.append(name)
        print(f"FAIL: {name} - {type(exc).__name__}: {exc}")
        traceback.print_exc()

with tempfile.TemporaryDirectory(prefix="cirt_phase6f_final_") as temp:
    os.environ["CIRT_DFIR_DB_PATH"] = str(Path(temp) / "integration.sqlite")

    def health():
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            r = client.get("/api/v1/health")
            assert r.status_code == 200, r.text
            j = r.json()
            assert j.get("status") == "ok", j
            assert j.get("mode") == "development-scaffold", j
            return "HTTP 200; development scaffold"

    def demo_cases():
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            r = client.get("/api/v1/demo/cases")
            assert r.status_code == 200, r.text
            items = r.json()
            assert len(items) == 3, items
            assert all(x["case_id"].startswith("DEMO-") for x in items), items
            return "HTTP 200; three synthetic cases"

    def audit_consistency():
        from app.case_store import list_demo_cases, DB_PATH
        from app.case_repository import connect
        items = list_demo_cases()
        assert len(items) == 3
        db = connect(DB_PATH)
        try:
            n = db.execute(
                "SELECT COUNT(*) FROM audit_events WHERE case_id LIKE 'DEMO-%'"
            ).fetchone()[0]
            assert n == 3, f"Expected 3 audit events; got {n}"
            return "Three demo cases and three creation audit events"
        finally:
            db.close()

    def audit_triggers():
        from app.case_store import DB_PATH
        from app.case_repository import connect
        db = connect(DB_PATH)
        try:
            names = {
                row["name"] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                ).fetchall()
            }
            required = {"audit_events_no_update", "audit_events_no_delete"}
            assert required.issubset(names), f"Missing triggers: {required - names}"
            return "Update/delete protection triggers exist"
        finally:
            db.close()

    def repository_tests():
        import test_case_repository
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_case_repository)
        result = unittest.TestResult()
        suite.run(result)
        if not result.wasSuccessful():
            raise AssertionError(
                f"Ran {result.testsRun}; failures={result.failures}; errors={result.errors}"
            )
        return f"{result.testsRun} repository tests passed"

    def api_wiring():
        source = (BACKEND / "app" / "main.py").read_text(encoding="utf-8")
        assert "from app.case_store import list_demo_cases" in source
        assert "list_demo_cases()" in source
        return "API source references the database-backed case store"

    check("API health endpoint", health)
    check("Synthetic demo-case endpoint", demo_cases)
    check("Database/audit consistency", audit_consistency)
    check("Audit protection triggers", audit_triggers)
    check("Repository unit tests", repository_tests)
    check("API-to-store wiring", api_wiring)

    os.environ.pop("CIRT_DFIR_DB_PATH", None)

print(f"\nPhase 6F checks: {len(passed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)