from pathlib import Path
import os
import subprocess
import sys

root = Path.cwd()
project = root.parent.parent
app = root / "app"

required_env = [
    "CIRT_DFIR_ENTRA_TENANT_ID",
    "CIRT_DFIR_ENTRA_EXPECTED_ISSUER",
    "CIRT_DFIR_ENTRA_AUDIENCE",
]

auth_file = app / "auth_dependencies.py"
main_file = app / "main.py"
authenticator_file = app / "entra_authenticator.py"
tests_dir = root / "tests"

print("CIRT-DFIR - PHASE 8B186")
print("Authentication integration readiness gate")
print("Read-only source/config inspection plus full backend test suite.")
print("Environment variable values and credentials will NOT be printed.")
print()

problems = []

def read_source(path):
    if not path.is_file():
        problems.append(f"Required source file missing: {path.name}")
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")

auth_source = read_source(auth_file)
main_source = read_source(main_file)
authenticator_source = read_source(authenticator_file)

print("=" * 72)
print("1. FAIL-CLOSED AUTHENTICATION GATE")
print("=" * 72)

fail_closed = (
    "get_current_principal" in auth_source
    and "HTTPException" in auth_source
    and "status_code=401" in auth_source
    and "require_permission" in auth_source
)

print("Auth dependency source present:", auth_file.is_file())
print("Fail-closed source markers present:", fail_closed)

if not fail_closed:
    problems.append("Fail-closed auth source markers require manual review.")

print()
print("=" * 72)
print("2. FASTAPI AUTHENTICATION WIRING")
print("=" * 72)

route_guard = (
    "require_permission" in main_source
    and "Depends(require_permission(" in main_source
)

entra_imports = any(
    marker in main_source
    for marker in (
        "from app.entra_authenticator import",
        "from app.entra_bearer_adapter import",
        "create_entra_authenticator(",
    )
)

explicitly_unwired = "NOT wired into FastAPI" in authenticator_source

print("Protected route dependency markers present:", route_guard)
print("Direct Entra integration markers in main.py:", entra_imports)
print("Authenticator explicitly says not wired:", explicitly_unwired)

if not route_guard:
    problems.append("Protected route dependency markers need review.")

if not entra_imports or explicitly_unwired:
    problems.append("Entra integration is not established; do not enable authentication.")

print()
print("=" * 72)
print("3. REQUIRED CONFIGURATION PRESENCE")
print("=" * 72)

missing = []
for name in required_env:
    present = bool(os.environ.get(name, "").strip())
    print(f"{name}: {'PRESENT' if present else 'MISSING OR EMPTY'}")
    if not present:
        missing.append(name)

if missing:
    problems.append("One or more required Entra environment variables are missing.")

env_example = project / ".env.example"
backend_env_example = root / ".env.example"

print("Project .env.example exists:", env_example.is_file())
print("Backend .env.example exists:", backend_env_example.is_file())
print("No .env file contents were read.")

print()
print("=" * 72)
print("4. FULL BACKEND TEST SUITE")
print("=" * 72)

if not tests_dir.is_dir():
    print("ERROR: tests directory not found.")
    print("FINAL STATUS: BLOCKED")
    sys.exit(2)

command = [sys.executable, "-m", "pytest", "-q", str(tests_dir)]
print("Running pytest against:", tests_dir)
print("Command:", " ".join(command))
print()

result = subprocess.run(command, cwd=str(root), check=False)
print()
print("PYTEST_EXIT_CODE:", result.returncode)

if result.returncode != 0:
    problems.append("Full backend test suite failed or could not complete.")

print()
print("=" * 72)
print("5. FINAL READINESS DECISION")
print("=" * 72)

if problems:
    print("STATUS: BLOCKED / REVIEW REQUIRED")
    for problem in problems:
        print("- " + problem)
else:
    print("STATUS: CHECKS PASSED")
    print("This check does not replace formal security approval.")

print()
print("No application source, configuration, or environment variables were changed.")
print("No tenant IDs, issuer values, audiences, tokens, or secrets were printed.")
print("This is not proof of production readiness.")
sys.exit(result.returncode)
