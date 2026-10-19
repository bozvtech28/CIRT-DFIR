from pathlib import Path
import subprocess
import sys

root = Path.cwd()
excluded = {
    ".venv", ".venv_phase8b161", "__pycache__",
    ".pytest_cache", "node_modules",
}

needles = (
    "validate_entra_config",
    "EntraAuthConfig",
    "create_entra_authenticator",
    "entra_config_preflight",
)

print("CIRT-DFIR - PHASE 8B185")
print("Focused Entra configuration regression tests")
print("No application or environment changes are intended.")
print()

test_root = root / "tests"
if not test_root.is_dir():
    print("ERROR: backend tests directory not found.")
    sys.exit(2)

candidates = []
for path in sorted(test_root.rglob("test_*.py")):
    if any(part in excluded for part in path.parts):
        continue
    try:
        content = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        continue
    if any(needle in content for needle in needles):
        candidates.append(path)

print("Matching test files:")
for path in candidates:
    print(" -", path.relative_to(root))

if not candidates:
    print()
    print("RESULT: BLOCKED - no focused test files found.")
    print("No tests were executed.")
    sys.exit(3)

print()
print("Executing focused tests with the project virtual environment:")
command = [
    sys.executable, "-m", "pytest", "-q",
    *[str(path) for path in candidates],
]
print("Command:", " ".join(command))
print("=" * 78)
result = subprocess.run(command, cwd=str(root), check=False)
print("=" * 78)
print("PYTEST_EXIT_CODE:", result.returncode)

if result.returncode == 0:
    print("RESULT: PASS - all discovered focused test files passed.")
else:
    print("RESULT: FAIL - inspect the test output before any further changes.")

print("STATUS: TESTS ONLY; no application files or environment variables changed.")
sys.exit(result.returncode)
