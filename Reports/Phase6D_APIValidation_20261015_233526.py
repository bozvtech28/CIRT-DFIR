import os
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend")
sys.path.insert(0, r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend\\tests")

with tempfile.TemporaryDirectory(prefix="cirt_phase6d_") as temp_dir:
    os.environ["CIRT_DFIR_DB_PATH"] = str(Path(temp_dir) / "frontend_compat.sqlite")

    try:
        import test_api
        from fastapi.testclient import TestClient
        from app.main import app

        tests = [
            test_api.test_health_endpoint,
            test_api.test_demo_cases_are_synthetic,
        ]

        failures = 0
        for test in tests:
            try:
                test()
                print(f"PASS: {test.__name__}")
            except Exception:
                failures += 1
                print(f"FAIL: {test.__name__}")
                traceback.print_exc()

        try:
            from app.case_store import list_demo_cases
            cases = list_demo_cases()
            assert len(cases) == 3
            with TestClient(app) as client:
                response = client.get("/api/v1/demo/cases")
                assert response.status_code == 200
                assert len(response.json()) == 3
            print("PASS: database-backed API returns three synthetic cases")
        except Exception:
            failures += 1
            print("FAIL: database-backed API compatibility check")
            traceback.print_exc()

        print(f"\nAPI checks failed: {failures}")
        sys.exit(1 if failures else 0)
    finally:
        os.environ.pop("CIRT_DFIR_DB_PATH", None)