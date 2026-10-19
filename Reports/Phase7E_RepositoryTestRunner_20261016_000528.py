import importlib.util
import sys
import unittest
from pathlib import Path

backend_app = Path(sys.argv[1]).resolve()
design_dir = Path(sys.argv[2]).resolve()
test_file = Path(sys.argv[3]).resolve()

sys.path.insert(0, str(backend_app))
sys.path.insert(1, str(design_dir))

spec = importlib.util.spec_from_file_location("phase7e_repository_tests", test_file)
if spec is None or spec.loader is None:
    print("Could not load repository test module.")
    raise SystemExit(2)

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

suite = unittest.defaultTestLoader.loadTestsFromModule(module)
result = unittest.TextTestRunner(verbosity=2).run(suite)

print(
    f"PHASE7E_REPO_SUMMARY ran={result.testsRun}; "
    f"failures={len(result.failures)}; errors={len(result.errors)}"
)
raise SystemExit(0 if result.wasSuccessful() else 1)