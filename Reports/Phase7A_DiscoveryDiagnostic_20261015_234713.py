import importlib.util
import inspect
import sys
from pathlib import Path

design = Path(sys.argv[1])
test_file = Path(sys.argv[2])
repo_file = Path(sys.argv[3])

sys.path.insert(0, str(design))

print("=== REPOSITORY FUNCTION ===")
repo_text = repo_file.read_text(encoding="utf-8")
print("update_case present:", "def update_case(" in repo_text)

print("\n=== TEST FILE STRUCTURE ===")
lines = test_file.read_text(encoding="utf-8").splitlines()
for number, line in enumerate(lines, 1):
    stripped = line.lstrip()
    if stripped.startswith("class ") or stripped.startswith("def test_") or stripped.startswith("    def test_"):
        print(f"{number:04d}: indent={len(line) - len(stripped)} | {line}")

print("\n=== UNITTEST DISCOVERY ===")
spec = importlib.util.spec_from_file_location("test_case_repository", test_file)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

suite = __import__("unittest").defaultTestLoader.loadTestsFromModule(module)
tests = list(suite)
print("Top-level suite count:", suite.countTestCases())

for cls_name, cls in inspect.getmembers(module, inspect.isclass):
    if cls.__module__ == module.__name__:
        methods = [
            name for name, member in inspect.getmembers(cls, inspect.isfunction)
            if name.startswith("test")
        ]
        if methods:
            print(f"Class {cls_name}: {len(methods)} tests")
            for name in methods:
                print("  " + name)

print("\n=== LIFECYCLE TEST DEFINITIONS ===")
for name in [
    "test_update_case_records_before_and_after_audit",
    "test_update_missing_case_returns_none",
    "test_update_rejects_invalid_status",
    "test_update_rejects_empty_actor",
    "test_update_rejects_no_change",
]:
    obj = getattr(module, name, None)
    print(f"{name}: module-level function={callable(obj)}")