from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import re
import sys

ROOT = Path(r"C:\Users\BOZVLENOVO7\Desktop\PROJECT\CIRT_DFIR_Professional")
REPORT_DIR = ROOT / "Reports"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = REPORT_DIR / f"Phase8B2_AccessControlDesign_{STAMP}.txt"
MAIN = ROOT / "platform/backend/app/main.py"
REQ = ROOT / "platform/backend/requirements.txt"

if not MAIN.is_file():
    print(f"ERROR: Missing {MAIN}", file=sys.stderr)
    sys.exit(2)

main_text = MAIN.read_text(encoding="utf-8-sig", errors="replace")
requirements_text = REQ.read_text(encoding="utf-8-sig", errors="replace") if REQ.is_file() else ""

lines = []
def log(value=""):
    lines.append(str(value))

log("CIRT DFIR PROFESSIONAL — PHASE 8B.2")
log("Proposed Access-Control Design")
log(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}")
log("DESIGN ONLY — application source and database are not modified.")
log("")

log("1. CURRENT API ROUTES")
try:
    tree = ast.parse(main_text)
except SyntaxError as exc:
    log(f"ERROR: main.py syntax error: {exc}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(3)

routes = []
for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
            continue
        if not isinstance(dec.func.value, ast.Name) or dec.func.value.id not in {"app", "router"}:
            continue
        if dec.func.attr.lower() not in {"get", "post", "put", "patch", "delete"}:
            continue
        path = str(dec.args[0].value) if dec.args and isinstance(dec.args[0], ast.Constant) else "unknown"
        routes.append((dec.func.attr.upper(), path, node.name))
for method, path, handler in sorted(routes):
    log(f"{method} {path} -> {handler}")
if not routes:
    log("No routes detected; manual review required.")

log("")
log("2. PROPOSED ROLE MATRIX")
log("Route / Capability | Public | Viewer | DFIR Analyst | Administrator")
log("GET /api/v1/health | ALLOW | ALLOW | ALLOW | ALLOW")
log("GET /api/v1/demo/cases | DENY | ALLOW | ALLOW | ALLOW")
log("PATCH /api/v1/cases/{case_id} | DENY | DENY | ALLOW | ALLOW")
log("User/role administration (future) | DENY | DENY | DENY | ALLOW")
log("Audit review (future dedicated endpoint) | DENY | DENY | ALLOW* | ALLOW")
log("*Whether analysts may read audit history must be confirmed by the project owner.")
log("")

log("3. AUTHENTICATION DESIGN OPTIONS")
log("Preferred initial direction: a documented identity and session strategy chosen for the actual deployment environment.")
log("If deployed as a browser-based application, evaluate secure server-managed sessions with HttpOnly, Secure, and appropriate SameSite cookies, plus CSRF protection for state-changing requests.")
log("If deployed as an API for multiple clients, evaluate a supported identity provider or a carefully implemented token-based design with expiry, issuer/audience validation, and secure key management.")
log("Do not store plaintext passwords, tokens, signing keys, or credentials in source code.")
log("Use a maintained password-hashing implementation such as Argon2id if local password storage is selected; do not implement password hashing manually.")
log("Do not add authentication dependencies until the deployment model and identity source are confirmed.")
log("")

log("4. REQUIRED AUTHORIZATION BEHAVIOR")
log("- Authentication must be enforced server-side, not only by hiding frontend controls.")
log("- Every protected route must reject missing or invalid credentials.")
log("- Valid users with insufficient permissions must be denied.")
log("- Case updates must continue validating allowed status/severity values.")
log("- Record the authenticated actor identity in audit events; do not trust a client-supplied actor ID.")
log("- Do not permit unauthenticated user registration or privilege escalation.")
log("- Keep health endpoint output minimal and avoid exposing secrets or environment details.")
log("")

log("5. SECURITY TEST PLAN")
for item in [
    "Unauthenticated request to protected case-list endpoint is rejected.",
    "Unauthenticated PATCH request is rejected and does not mutate a case.",
    "Viewer PATCH request is rejected and does not mutate a case.",
    "Analyst PATCH request succeeds for an authorized synthetic case.",
    "Administrator can access explicitly approved administrative actions.",
    "Invalid, expired, or malformed credentials are rejected.",
    "Audit actor identity comes from the authenticated principal.",
    "CSRF defenses are tested if cookie-based authentication is chosen.",
    "Existing health behavior and frontend build remain compatible.",
    "All tests use temporary SQLite databases and synthetic records."
]:
    log(f"- {item}")
log("")

log("6. DEPENDENCY DECLARATION CHECK")
if REQ.is_file():
    log(f"requirements.txt SHA256: {hashlib.sha256(REQ.read_bytes()).hexdigest()}")
    log("Requirements entries (BOM-safe read):")
    for raw in requirements_text.splitlines():
        value = raw.strip()
        if value and not value.startswith("#"):
            log(f"  {value}")
    normalized = {
        re.match(r"([A-Za-z0-9_.-]+)", value).group(1).lower().replace("_", "-")
        for value in requirements_text.splitlines()
        if value.strip() and not value.lstrip().startswith("#")
        and re.match(r"([A-Za-z0-9_.-]+)", value.strip())
    }
    log(f"FastAPI declaration detected: {'fastapi' in normalized}")
else:
    log("requirements.txt not found.")

log("")
log("7. IMPLEMENTATION GATES")
log("Gate 1: Confirm intended deployment: local single-user, trusted internal network, or multi-user deployment.")
log("Gate 2: Confirm identity source: existing organizational identity provider or locally managed accounts.")
log("Gate 3: Approve roles and permissions, especially audit-history access.")
log("Gate 4: Select session/token strategy and required dependencies.")
log("Gate 5: Back up sources, implement authentication, and test using synthetic data.")
log("Gate 6: Run repository tests, API security tests, and frontend production build.")
log("")
log("8. SAFETY")
log("This report is a proposal, not implemented access control.")
log("No application source, database, collector, or evidence files were modified.")
log("No server was started, no packages were installed, and no network requests were made.")

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nREPORT_PATH={REPORT}")
