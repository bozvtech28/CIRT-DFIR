import ast
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
design = root / "platform" / "database-design"
backend = root / "platform" / "backend"
frontend = root / "platform" / "frontend"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def function_source(path, function_name):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            lines = text.splitlines()
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
    return None

design_repo = design / "case_repository.py"
backend_repo = backend / "app" / "case_repository.py"
design_schema = design / "phase6_schema.sql"
backend_schema = backend / "app" / "case_schema.sql"

print("=== REPOSITORY HASHES ===")
print("Design :", sha(design_repo))
print("Backend:", sha(backend_repo))
print("Same repository:", sha(design_repo) == sha(backend_repo))

print("\n=== update_case FUNCTION PRESENCE ===")
for label, path in [("Design", design_repo), ("Backend", backend_repo)]:
    function = function_source(path, "update_case")
    print(f"{label}: {'PRESENT' if function else 'ABSENT'}")
    if function:
        print(function)

print("\n=== SCHEMA HASHES ===")
print("Design :", sha(design_schema))
print("Backend:", sha(backend_schema))
print("Same schema:", sha(design_schema) == sha(backend_schema))

print("\n=== FRONTEND API REFERENCES ===")
app = frontend / "src" / "App.tsx"
lines = app.read_text(encoding="utf-8").splitlines()
for number, line in enumerate(lines, 1):
    if any(term in line.lower() for term in ("api", "fetch(", "axios", "demo/cases")):
        print(f"{number:04d}: {line.strip()}")

print("\n=== VITE PROXY ===")
vite = frontend / "vite.config.ts"
print(vite.read_text(encoding="utf-8"))

print("\nREVIEW ONLY: no source files modified and no server started.")