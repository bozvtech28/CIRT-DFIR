import sys
import traceback

sys.path.insert(0, r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend")
sys.path.insert(0, r"C:\\Users\\BOZVLENOVO7\\Desktop\\PROJECT\\CIRT_DFIR_Professional\\platform\\backend\\tests")

import test_api

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

print(f"\nRan {len(tests)} API tests")
print(f"Failures: {failures}")
sys.exit(1 if failures else 0)