from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.metadata as metadata
import re
import sys

ROOT = Path(r"C:\Users\BOZVLENOVO7\Desktop\PROJECT\CIRT_DFIR_Professional")
REPORT_DIR = ROOT / "Reports"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = REPORT_DIR / f"Phase8B1_APIAuthReadiness_{STAMP}.txt"

MAIN = ROOT / "platform/backend/app/main.py"
REQUIREMENTS = ROOT / "platform/backend/requirements.txt"
VITE = ROOT / "platform/frontend/vite.config.ts"

lines = []
def log(value=""):
    lines.append(str(value))

log("CIRT DFIR PROFESSIONAL — PHASE 8B.1")
log("API Authentication Readiness and Dependency Verification")
log(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}")
log("Static inspection only; no server or network requests.")
log("")

if not MAIN.is_file():
    print(f"ERROR: Missing backend API source: {MAIN}", file=sys.stderr)
    sys.exit(2)

main_text = MAIN.read_text(encoding="utf-8", errors="replace")
requirements_text = REQUIREMENTS.read_text(encoding="utf-8", errors="replace") if REQUIREMENTS.is_file() else ""
vite_text = VITE.read_text(encoding="utf-8", errors="replace") if VITE.is_file() else ""

log("1. SOURCE FILE HASHES")
for path in [MAIN, REQUIREMENTS, VITE]:
    if path.is_file():
        log(f"{path.relative_to(ROOT)} | SHA256={hashlib.sha256(path.read_bytes()).hexdigest()}")
    else:
        log(f"{path.relative_to(ROOT)} | MISSING")

log("")
log("2. API ROUTE AND HANDLER INSPECTION")
try:
    tree = ast.parse(main_text)
except SyntaxError as exc:
    log(f"ERROR: main.py cannot be parsed: {exc}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(3)

routes = []
for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        if not isinstance(func, ast.Attribute) or func.attr.lower() not in {
            "get", "post", "put", "patch", "delete", "options", "head"
        }:
            continue
        if not isinstance(func.value, ast.Name) or func.value.id not in {"app", "router"}:
            continue

        path_value = "dynamic/unknown"
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            path_value = str(decorator.args[0].value)

        signature_parts = []
        has_auth_dependency = False
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.arg in {"self", "cls"}:
                continue
            default = None
            combined_defaults = list(node.args.defaults)
            if combined_defaults:
                offset = len(node.args.args) - len(combined_defaults)
                index = node.args.args.index(arg) if arg in node.args.args else -1
                if index >= offset and index >= 0:
                    default = combined_defaults[index - offset]
            if arg in node.args.kwonlyargs:
                kw_index = node.args.kwonlyargs.index(arg)
                if kw_index < len(node.args.kw_defaults):
                    default = node.args.kw_defaults[kw_index]
            default_text = ast.unparse(default) if default is not None else ""
            signature_parts.append(f"{arg.arg}{'=' + default_text if default_text else ''}")
            if default is not None and re.search(r"\b(Depends|Security)\s*\(", default_text):
                has_auth_dependency = True

        routes.append({
            "method": func.attr.upper(),
            "path": path_value,
            "name": node.name,
            "line": node.lineno,
            "params": signature_parts,
            "dependency": has_auth_dependency,
        })

for route in sorted(routes, key=lambda r: r["line"]):
    log(f"ROUTE: {route['method']} {route['path']}")
    log(f"  Handler: {route['name']} (line {route['line']})")
    log(f"  Parameters: {', '.join(route['params']) or '(none)'}")
    log(f"  Depends/Security in parameter defaults: {route['dependency']}")

if not routes:
    log("No app/router HTTP route decorators detected.")

log("")
log("3. GLOBAL AUTHENTICATION / AUTHORIZATION INDICATORS")
try:
    top_level_calls = []
    for node in tree.body:
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                try:
                    top_level_calls.append(ast.unparse(item))
                except Exception:
                    pass
    global_security = [
        call for call in top_level_calls
        if re.search(r"(add_middleware|include_router|Depends|Security|OAuth2|HTTPBearer|HTTPBasic|AuthenticationMiddleware)", call, re.I)
    ]
    for call in sorted(set(global_security)):
        log(f"INDICATOR: {call}")
    if not global_security:
        log("No common global authentication/dependency indicators detected by this static scan.")
except Exception as exc:
    log(f"Global indicator scan could not complete: {exc}")

log("")
log("4. INSTALLED BACKEND DISTRIBUTIONS")
installed = {}
for dist in metadata.distributions():
    name = dist.metadata.get("Name")
    version = dist.version
    if name:
        installed[name.lower().replace("_", "-")] = version

for name in ["fastapi", "starlette", "pydantic", "uvicorn", "pytest", "python-jose", "PyJWT", "passlib", "bcrypt", "argon2-cffi", "cryptography"]:
    key = name.lower().replace("_", "-")
    log(f"{name}: {installed.get(key, 'NOT INSTALLED in this Python environment')}")

log("")
log("5. REQUIREMENTS DECLARATION")
if not REQUIREMENTS.is_file():
    log("requirements.txt is missing.")
else:
    for raw in requirements_text.splitlines():
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            log(f"DECLARED: {stripped}")
    declared_names = set()
    for raw in requirements_text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)", stripped)
        if match:
            declared_names.add(match.group(1).lower().replace("_", "-"))
    for package in ["fastapi", "pydantic", "uvicorn"]:
        log(f"DECLARED CHECK {package}: {package in declared_names}")

log("")
log("6. FRONTEND DEVELOPMENT PROXY")
if vite_text:
    for line_number, line in enumerate(vite_text.splitlines(), start=1):
        if re.search(r"proxy|target|host|strictPort", line, re.I):
            log(f"vite.config.ts:{line_number}: {line.strip()}")
else:
    log("vite.config.ts missing.")

log("")
log("7. REVIEW NOTES")
log("- A route without an obvious Depends/Security parameter is not proof by itself that the route is unprotected; inspect dependencies and middleware manually.")
log("- Package installation is not the same as a dependency being declared in requirements.txt.")
log("- Do not add authentication libraries until the current deployment model and identity source are chosen.")
log("- For the next implementation phase, define roles and route permissions before coding.")
log("- Use temporary databases and synthetic cases for security tests.")
log("- No application source, database, collector, or evidence files were modified by this Python assessment.")
log("- This script does not start the API, install packages, or send network requests.")

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nREPORT_PATH={REPORT}")
