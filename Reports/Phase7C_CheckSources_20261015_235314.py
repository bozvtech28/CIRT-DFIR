import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
design = root / "platform" / "database-design"
backend = root / "platform" / "backend"
frontend = root / "platform" / "frontend"

checks = []

def record(name, ok, detail):
    checks.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL") + " | " + name + " | " + detail)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

design_repo = design / "case_repository.py"
backend_repo = backend / "app" / "case_repository.py"
design_schema = design / "phase6_schema.sql"
backend_schema = backend / "app" / "case_schema.sql"

record(
    "Repository source parity",
    sha256(design_repo) == sha256(backend_repo),
    f"design={sha256(design_repo)}; backend={sha256(backend_repo)}",
)
record(
    "Schema source parity",
    sha256(design_schema) == sha256(backend_schema),
    f"design={sha256(design_schema)}; backend={sha256(backend_schema)}",
)

repo_text = design_repo.read_text(encoding="utf-8")
schema_text = design_schema.read_text(encoding="utf-8")
store_text = (backend / "app" / "case_store.py").read_text(encoding="utf-8")
main_text = (backend / "app" / "main.py").read_text(encoding="utf-8")
app_text = (frontend / "src" / "App.tsx").read_text(encoding="utf-8")

record(
    "Repository update function exists",
    "def update_case(" in repo_text,
    "Design repository update_case() definition checked",
)
record(
    "Audit update event exists",
    '"CASE_UPDATED"' in repo_text or "'CASE_UPDATED'" in repo_text,
    "Repository source checked for CASE_UPDATED event",
)
record(
    "Audit append-only triggers exist",
    "audit_events_no_update" in schema_text and "audit_events_no_delete" in schema_text,
    "Design schema checked for update/delete protection triggers",
)
record(
    "Backend uses case store",
    "list_demo_cases" in main_text and "from app.case_store import" in main_text,
    "Current API wiring inspected; no source changed",
)
record(
    "Case store has database path override",
    "CIRT_DFIR_DB_PATH" in store_text,
    "Environment-based database path override checked",
)
record(
    "Frontend uses relative API paths",
    '"/api/v1/demo/cases"' in app_text or "'/api/v1/demo/cases'" in app_text,
    "Frontend source checked for relative demo-case endpoint",
)
record(
    "BozV footer signature preserved",
    "Developed by:" in app_text and "Powered by:" in app_text,
    "Both signature labels found in frontend source",
)

print()
passed = sum(1 for _, ok, _ in checks if ok)
failed = len(checks) - passed
print(f"SUMMARY | Passed={passed} | Failed={failed} | Total={len(checks)}")
print("NOTE | A failed parity check is a review item, not an automatic instruction to overwrite files.")
sys.exit(1 if failed else 0)