import ast
import hashlib
import sys
from pathlib import Path

design_repo, backend_repo, design_schema, backend_schema, main_file, app_file = [
    Path(p) for p in sys.argv[1:]
]
checks = []

def record(name, passed, detail):
    checks.append((name, bool(passed)))
    print(f"{'PASS' if passed else 'FAIL'} | {name} | {detail}")

def functions(tree):
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

def non_functions(tree):
    return [
        ast.dump(node, include_attributes=False)
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

def has_route(tree, method, route):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute) or func.attr.lower() != method.lower():
                continue
            if not decorator.args:
                continue
            first = decorator.args[0]
            if isinstance(first, ast.Constant) and first.value == route:
                return True
    return False

try:
    dt = ast.parse(design_repo.read_text(encoding="utf-8"))
    bt = ast.parse(backend_repo.read_text(encoding="utf-8"))

    df = functions(dt)
    bf = functions(bt)
    record("Repository function parity", df == bf,
           f"design={sorted(df)}; backend={sorted(bf)}")
    record("Repository module-level parity", non_functions(dt) == non_functions(bt),
           "Compared non-function top-level syntax nodes")

    ds = design_schema.read_bytes()
    bs = backend_schema.read_bytes()
    record("SQL schema byte parity", ds == bs,
           f"design_sha256={hashlib.sha256(ds).hexdigest()}; "
           f"backend_sha256={hashlib.sha256(bs).hexdigest()}")

    schema = ds.decode("utf-8").upper()
    idempotent = all(x in schema for x in (
        "CREATE TABLE IF NOT EXISTS",
        "CREATE INDEX IF NOT EXISTS",
        "CREATE TRIGGER IF NOT EXISTS",
    ))
    record("Schema idempotency declarations", idempotent,
           "Checks TABLE, INDEX and TRIGGER IF NOT EXISTS")

    main_text = main_file.read_text(encoding="utf-8")
    mt = ast.parse(main_text)

    record("PATCH case-update endpoint",
           has_route(mt, "patch", "/api/v1/cases/{case_id}"),
           "PATCH /api/v1/cases/{case_id}")

    record("HTTP error mapping",
           'message == "Update contains no case changes."' in main_text
           and "status_code=409" in main_text
           and "status_code=422" in main_text,
           "No-change=409; other ValueError=422")

    record("Health endpoint", has_route(mt, "get", "/api/v1/health"),
           "GET /api/v1/health")
    record("Synthetic demo-case endpoint",
           has_route(mt, "get", "/api/v1/demo/cases"),
           "GET /api/v1/demo/cases")

    ui = app_file.read_text(encoding="utf-8")
    record("BozV signature",
           "Developed by:" in ui and "Powered by:" in ui and "BozV" in ui,
           "Developer and powered-by labels checked")
    record("Relative API request",
           "/api/v1/demo/cases" in ui,
           "Frontend references demo-case API")

except Exception as exc:
    record("Source validation execution", False, repr(exc))

passed = sum(value for _, value in checks)
failed = len(checks) - passed
print(f"PHASE7E1_SUMMARY passed={passed}; failed={failed}; total={len(checks)}")
sys.exit(0 if checks and failed == 0 else 1)