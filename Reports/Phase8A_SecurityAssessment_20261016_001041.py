from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import re
import sys

ROOT = Path(r"C:\Users\BOZVLENOVO7\Desktop\PROJECT\CIRT_DFIR_Professional")
REPORT_DIR = ROOT / "Reports"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = REPORT_DIR / f"Phase8A_SecurityAssessment_{STAMP}.txt"

TARGETS = [
    "platform/backend/app/main.py",
    "platform/backend/app/case_store.py",
    "platform/backend/app/case_repository.py",
    "platform/backend/app/case_schema.sql",
    "platform/backend/requirements.txt",
    "platform/frontend/src/App.tsx",
    "platform/frontend/vite.config.ts",
    "platform/frontend/package.json",
    "README.md",
    "docs/Architecture.md",
    "docs/Requirements.md",
]

lines = []
checks = []

def log(text=""):
    lines.append(str(text))

def check(name, passed, detail):
    checks.append((name, bool(passed), detail))
    log(f"[{'PASS' if passed else 'REVIEW'}] {name}: {detail}")

log("CIRT DFIR PROFESSIONAL — PHASE 8A")
log("Security Design and Read-Only Assessment")
log(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}")
log(f"Project root: {ROOT}")
log("Scope: static source/configuration inspection only")
log("")

if not ROOT.is_dir():
    print(f"ERROR: Project root not found: {ROOT}", file=sys.stderr)
    sys.exit(2)

content = {}
for relative in TARGETS:
    path = ROOT / relative
    if path.is_file():
        try:
            content[relative] = path.read_text(encoding="utf-8", errors="replace")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            log(f"FILE FOUND | {relative} | SHA256={digest}")
        except OSError as exc:
            log(f"FILE READ ERROR | {relative} | {exc}")
    else:
        log(f"FILE MISSING | {relative}")

log("")
log("1. BACKEND ROUTE INVENTORY")
main_rel = "platform/backend/app/main.py"
main_text = content.get(main_rel, "")
routes = []
auth_dependencies = []
middleware = []

if main_text:
    try:
        tree = ast.parse(main_text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    try:
                        rendered = ast.unparse(decorator)
                    except Exception:
                        rendered = ""
                    if re.search(r"\.(get|post|put|patch|delete|options|head)\s*\(", rendered):
                        routes.append((rendered, node.name, node.lineno))
            if isinstance(node, ast.Call):
                try:
                    rendered = ast.unparse(node)
                except Exception:
                    rendered = ""
                if re.search(r"(include_router|Depends|Security)\s*\(", rendered):
                    auth_dependencies.append((rendered, getattr(node, "lineno", "?")))
                if re.search(r"(add_middleware|middleware)\s*\(", rendered, re.I):
                    middleware.append((rendered, getattr(node, "lineno", "?")))
    except SyntaxError as exc:
        log(f"Could not parse main.py: {exc}")

for decorator, function, lineno in sorted(routes, key=lambda item: item[2] if isinstance(item[2], int) else 0):
    log(f"ROUTE | line {lineno} | {decorator} | function={function}")

if not routes:
    log("No FastAPI-style route decorators detected by the static scanner.")

log("")
log("2. SECURITY CONTROL INDICATORS")
all_source = "\n".join(content.values())
checks_patterns = [
    ("Authentication indicators", r"\b(authenticate|authentication|OAuth2PasswordBearer|HTTPBearer|HTTPBasic|OpenIDConnect|login_required|current_user)\b"),
    ("Authorization / role indicators", r"\b(authorize|authorization|permission|permissions|role_required|RBAC|access_control|is_admin)\b"),
    ("Session / cookie security indicators", r"\b(SessionMiddleware|httponly|http_only|secure_cookie|SameSite|samesite|session_secret)\b"),
    ("CSRF protection indicators", r"\b(CSRFProtect|csrf_token|csrf_protect|double_submit_cookie)\b"),
    ("Rate limiting indicators", r"\b(limiter|slowapi|RateLimiter|rate_limit|rate-limiting)\b"),
    ("CORS configuration indicators", r"\b(CORSMiddleware|allow_origins|allow_credentials)\b"),
    ("Secret/configuration indicators", r"\b(os\.environ|getenv\(|BaseSettings|SecretStr|SECRET_KEY|API_KEY)\b"),
    ("Audit/hash-chain indicators", r"\b(previous_hash|event_hash|hashlib|hmac|signature|verify_chain|verify_hash)\b"),
    ("TLS / secure transport indicators", r"\b(https://|ssl_context|HTTPSRedirectMiddleware|Strict-Transport-Security)\b"),
]

for name, pattern in checks_patterns:
    matches = re.findall(pattern, all_source, flags=re.IGNORECASE)
    unique = sorted(set(matches), key=str.lower)
    check(name, bool(unique), ", ".join(unique[:12]) if unique else "No matching indicators found; manual review required")

log("")
log("3. API AND DATABASE OBSERVATIONS")
if main_text:
    for term, description in [
        ("HTTPException", "HTTP error handling"),
        ("ConfigDict(extra=\"forbid\")", "Pydantic unknown-field rejection"),
        ("@app.patch", "PATCH route"),
        ("Depends(", "FastAPI dependency injection"),
    ]:
        check(description, term.lower() in main_text.lower(), "Indicator found" if term.lower() in main_text.lower() else "Indicator not found in main.py")

schema = content.get("platform/backend/app/case_schema.sql", "")
repo = content.get("platform/backend/app/case_repository.py", "")
store = content.get("platform/backend/app/case_store.py", "")

check("Audit table declaration", bool(re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+audit_events", schema, re.I)),
      "audit_events table declaration found" if re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+audit_events", schema, re.I) else "Expected declaration not detected")
check("Audit update/delete triggers", bool(re.search(r"CREATE\s+TRIGGER\s+IF\s+NOT\s+EXISTS", schema, re.I) and re.search(r"BEFORE\s+(UPDATE|DELETE)", schema, re.I)),
      "At least one idempotent trigger and UPDATE/DELETE trigger pattern detected" if re.search(r"CREATE\s+TRIGGER\s+IF\s+NOT\s+EXISTS", schema, re.I) and re.search(r"BEFORE\s+(UPDATE|DELETE)", schema, re.I) else "Review trigger definitions manually")
check("Repository update auditing", "CASE_UPDATED" in repo and "audit" in repo.lower(),
      "CASE_UPDATED and audit-related code indicators found" if "CASE_UPDATED" in repo and "audit" in repo.lower() else "Expected update-audit indicators not both detected")
check("Database path override", "CIRT_DFIR_DB_PATH" in store,
      "Environment-variable database override detected" if "CIRT_DFIR_DB_PATH" in store else "Override not detected")
check("Default database location", "cirt_cases.sqlite" in store,
      "SQLite filename indicator found" if "cirt_cases.sqlite" in store else "SQLite filename indicator not found")

log("")
log("4. DEPENDENCY AND FRONTEND CONFIGURATION")
requirements = content.get("platform/backend/requirements.txt", "")
package = content.get("platform/frontend/package.json", "")
vite = content.get("platform/frontend/vite.config.ts", "")
for dependency in ["fastapi", "pydantic"]:
    check(f"Backend dependency: {dependency}", bool(re.search(rf"(?im)^\s*{dependency}\b", requirements)),
          "Listed in requirements.txt" if re.search(rf"(?im)^\s*{dependency}\b", requirements) else "Not detected in requirements.txt")
check("Frontend API proxy target", "127.0.0.1:8000" in vite,
      "Local development proxy target detected" if "127.0.0.1:8000" in vite else "Expected local proxy target not detected")
check("Frontend package manifest", bool(package.strip()),
      "package.json was read" if package.strip() else "package.json missing or empty")

log("")
log("5. REVIEW FINDINGS")
log("These are static indicators, not proof that a control is secure or operational.")
log("A keyword match may be a comment or unused code; absence of a match is not definitive proof of absence.")
log("")
log("Priority review items:")
log("P1 — Confirm whether every sensitive API endpoint requires authenticated identity.")
log("P1 — Define authorization rules for case creation, case updates, viewing, and audit access.")
log("P1 — Decide how credentials, secrets, and session/token lifetimes will be managed.")
log("P1 — Define the threat model for the SQLite database and audit records, including local administrator access.")
log("P2 — Specify secure deployment settings, including HTTPS, CORS policy, and rate limiting where applicable.")
log("P2 — Add negative tests for unauthenticated requests and insufficient privileges before enabling access controls.")
log("P2 — Keep all security tests on temporary databases and synthetic case records.")
log("")
log("6. SCOPE AND SAFETY")
log("No application source, database, collector, or evidence files were intentionally modified by this assessment.")
log("No server was started, no packages were installed, and no network requests were made.")
log("Only this assessment script and its report are written under Reports.")
log("")
log("7. SUMMARY")
passed = sum(1 for _, ok, _ in checks if ok)
review = len(checks) - passed
log(f"Indicators/checks marked PASS: {passed}")
log(f"Items requiring manual review: {review}")
log("This report is a design baseline, not a penetration test, compliance certification, or production-readiness approval.")

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nREPORT_PATH={REPORT}")
