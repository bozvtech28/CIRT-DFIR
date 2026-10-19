import ast
import hashlib
import sys
from pathlib import Path

design_repo = Path(sys.argv[1])
backend_repo = Path(sys.argv[2])
design_schema = Path(sys.argv[3])
backend_schema = Path(sys.argv[4])
app_file = Path(sys.argv[5])

checks = []

def record(name, passed, detail):
    checks.append((name, bool(passed), detail))
    print(f"{'PASS' if passed else 'FAIL'} | {name} | {detail}")

try:
    design_text = design_repo.read_text(encoding="utf-8")
    backend_text = backend_repo.read_text(encoding="utf-8")
    design_tree = ast.parse(design_text)
    backend_tree = ast.parse(backend_text)

    def node_key(node):
        return ast.dump(node, include_attributes=False)

    def function_map(tree):
        return {
            node.name: node_key(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def non_function_nodes(tree):
        return [
            node_key(node)
            for node in tree.body
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    design_functions = function_map(design_tree)
    backend_functions = function_map(backend_tree)

    record(
        "Repository function parity",
        design_functions == backend_functions,
        f"design_functions={sorted(design_functions)}; backend_functions={sorted(backend_functions)}"
    )

    record(
        "Repository module-level parity",
        non_function_nodes(design_tree) == non_function_nodes(backend_tree),
        "Non-function top-level AST nodes compared"
    )

    ds = design_schema.read_bytes()
    bs = backend_schema.read_bytes()
    record(
        "SQL schema byte parity",
        ds == bs,
        f"design_sha256={hashlib.sha256(ds).hexdigest()}; backend_sha256={hashlib.sha256(bs).hexdigest()}"
    )

    schema_text = ds.decode("utf-8")
    record(
        "Schema idempotency declarations",
        "CREATE TABLE IF NOT EXISTS" in schema_text.upper()
        and "CREATE INDEX IF NOT EXISTS" in schema_text.upper()
        and "CREATE TRIGGER IF NOT EXISTS" in schema_text.upper(),
        "Checks CREATE TABLE/INDEX/TRIGGER IF NOT EXISTS"
    )

    app_text = app_file.read_text(encoding="utf-8")
    app_tree = ast.parse(app_text)
    route_found = False
    update_found = False
    conflict_found = (
        'message == "Update contains no case changes."' in app_text
        and "status_code=409" in app_text
        and "status_code=422" in app_text
    )
    health_found = False
    demo_found = False

    for node in ast.walk(app_tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = [ast.unparse(d) for d in node.decorator_list]
            if node.name == "update_case_endpoint":
                update_found = True
                route_found = any(
                    'patch("/api/v1/cases/{case_id}"' in d
                    for d in decorators
                )
            if node.name == "health":
                health_found = any(
                    'get("/api/v1/health"' in d
                    for d in decorators
                )
            if node.name == "get_demo_cases":
                demo_found = any(
                    'get("/api/v1/demo/cases"' in d
                    for d in decorators
                )

    record(
        "PATCH case-update endpoint",
        update_found and route_found,
        "PATCH /api/v1/cases/{case_id}"
    )
    record(
        "HTTP error mapping",
        conflict_found,
        "No-change=409; other ValueError=422"
    )
    record("Health endpoint", health_found, "GET /api/v1/health")
    record("Synthetic demo-case endpoint", demo_found, "GET /api/v1/demo/cases")

    frontend_text = app_file.parent.parent.parent / "frontend" / "src" / "App.tsx"
    if frontend_text.exists():
        ui_text = frontend_text.read_text(encoding="utf-8")
        record(
            "BozV signature",
            "Developed by:" in ui_text and "Powered by:" in ui_text and "BozV" in ui_text,
            "Developer and powered-by labels checked"
        )
        record(
            "Relative API request",
            "/api/v1/demo/cases" in ui_text,
            "Frontend references demo-case API"
        )
    else:
        record("BozV signature", False, f"Frontend source not found: {frontend_text}")
        record("Relative API request", False, f"Frontend source not found: {frontend_text}")

except Exception as exc:
    record("Source validation execution", False, repr(exc))

print(f"PHASE7E_SOURCE_SUMMARY passed={sum(p for _, p, _ in checks)}; failed={sum(not p for _, p, _ in checks)}; total={len(checks)}")
sys.exit(0 if checks and all(p for _, p, _ in checks) else 1)