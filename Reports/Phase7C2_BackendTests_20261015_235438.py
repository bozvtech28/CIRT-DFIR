import importlib.util
import sys
import unittest
from pathlib import Path

backend_app = Path(sys.argv[1])
test_file = Path(sys.argv[2])

sys.path.insert(0, str(backend_app))

spec = importlib.util.spec_from_file_location("test_case_repository_backend", test_file)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

suite = unittest.defaultTestLoader.loadTestsFromModule(module)
count = suite.countTestCases()
print(f"BACKEND TEST DISCOVERY: {count} tests")

if count != 14:
    print("STOP: expected 14 tests.")
    raise SystemExit(5)

result = unittest.TextTestRunner(verbosity=2).run(suite)
print(f"BACKEND TEST SUMMARY: ran={result.testsRun}; failures={len(result.failures)}; errors={len(result.errors)}")
raise SystemExit(0 if result.wasSuccessful() else 1)