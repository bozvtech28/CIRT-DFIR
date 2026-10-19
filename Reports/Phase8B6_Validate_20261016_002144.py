import ast
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(r"C:\Users\BOZVLENOVO7\Desktop\PROJECT\CIRT_DFIR_Professional")
APP = ROOT / "platform/backend/app"
TESTS = ROOT / "platform/backend/tests"

if len(sys.argv) != 2:
    print("Usage: validation_script.py <report_path>")
    sys.exit(2)

REPORT = Path(sys.argv[1])
results = []

def check(name, passed, detail):
    results.append((name, bool(passed), str(detail)))

try:
    main_path = APP / "main.py"
    auth_path = APP / "auth_dependencies.py"
    security_path = APP / "security.py"

    main_text = main_path.read_text(encoding="utf-8-sig")
    auth_text = auth_path.read_text(encoding="utf-8-sig")
    security_text = security_path.read_text(encoding="utf-8-sig")
except Exception as exc:
    print(f"Unable to read required source: {exc}")
    sys.exit(2)

try:
    tree = ast.parse(main_text)
    check("API source syntax", True, "main.py parsed successfully")
except SyntaxError as exc:
    tree = None
    check("API source syntax", False, str(exc))

routes = {}
if tree:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                continue
            if not isinstance(dec.func.value, ast.Name) or dec.func.value.id != "app":
                continue
            method = dec.func.attr.upper()
            path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else "unknown"
            routes[(method, path)] = (node.name, dec)

expected = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/demo/cases"),
    ("PATCH", "/api/v1/cases/{case_id}"),
}
check("Expected API routes present", expected.issubset(routes), f"Discovered routes: {sorted(routes)}")

def decorator_has_permission(route_key, permission):
    if route_key not in routes:
        return False
    _, dec = routes[route_key]
    segment = ast.get_source_segment(main_text, dec) or ""
    return "require_permission" in segment and permission in segment and "Depends" in segment

check(
    "Demo case-list route requires cases:read",
    decorator_has_permission(("GET", "/api/v1/demo/cases"), "cases:read"),
    "Route dependency inspected",
)
check(
    "Case-update route requires cases:update",
    decorator_has_permission(("PATCH", "/api/v1/cases/{case_id}"), "cases:update"),
    "Route dependency inspected",
)

health_protected = False
if ("GET", "/api/v1/health") in routes:
    _, dec = routes[("GET", "/api/v1/health")]
    health_protected = "require_permission" in (ast.get_source_segment(main_text, dec) or "")
check("Health route remains outside case RBAC gate", not health_protected, "Health is intended to remain public")

check(
    "Authentication gate denies by default",
    "status_code=401" in auth_text and "Authentication is not configured" in auth_text,
    "Default dependency returns unauthorized",
)
check(
    "RBAC dependency invokes authorization policy",
    "authorize(principal, permission)" in auth_text and "status_code=403" in auth_text,
    "Authorization policy and forbidden response detected",
)
check(
    "RBAC policy module declares permissions",
    "PERMISSIONS" in security_text and "def authorize(" in security_text,
    "RBAC policy declarations detected",
)

for filename in ["test_api.py", "test_api_auth_gate.py", "test_security.py"]:
    path = TESTS / filename
    check(f"Test file exists: {filename}", path.is_file(), str(path))

gate_path = TESTS / "test_api_auth_gate.py"
if gate_path.is_file():
    gate_text = gate_path.read_text(encoding="utf-8-sig")
    for marker in [
        "test_demo_cases_reject_unauthenticated_request",
        "test_case_update_rejects_unauthenticated_request",
        "test_viewer_cannot_update_case",
        "test_admin_can_pass_case_update_authorization_gate",
    ]:
        check(f"Test defined: {marker}", marker in gate_text, "Expected test function")
else:
    check("Authentication gate tests readable", False, str(gate_path))

backup = ROOT / "Backups/Phase8B5_20261016_001906"
previous_report = ROOT / "Reports/Phase8B5_AuthGate_20261016_001906.txt"
check("Phase 8B.5 backup folder exists", backup.is_dir(), str(backup))
check("Phase 8B.5 main.py backup exists", (backup / "main.py").is_file(), "Pre-change source backup")
check("Previous Phase 8B.5 report exists", previous_report.is_file(), str(previous_report))

lines = [
    "CIRT DFIR PROFESSIONAL — PHASE 8B.6",
    "OIDC provider readiness and deployment safety validation",
    f"Generated UTC: {datetime.now(timezone.utc).isoformat()}",
    "Identity provider: NOT DECIDED",
    "Deployment target: INTERNAL ORGANIZATION NETWORK",
    "Static validation only; no server or identity-provider connection.",
    "",
    "CHECK RESULTS",
]
for name, passed, detail in results:
    lines.append(f"[{'PASS' if passed else 'FAIL'}] {name} — {detail}")

lines += [
    "",
    "IDENTITY PROVIDER DECISION MATRIX",
    "Microsoft Entra ID: consider if the organization already uses Microsoft Entra / Microsoft 365 for managed identities.",
    "Keycloak: consider if the organization operates or approves a self-hosted OIDC identity service.",
    "Other OIDC provider: require the official issuer, client registration, supported claims, and organizational approval.",
    "",
    "REQUIRED BEFORE PRODUCTION",
    "1. Obtain approval for the identity provider and account/role provisioning.",
    "2. Register the application and exact redirect URIs.",
    "3. Validate token signature, issuer, audience, expiry, and permitted algorithms.",
    "4. Map roles from validated claims or a server-controlled role store.",
    "5. Enforce authentication and RBAC on every protected API route.",
    "6. Test invalid, expired, wrong-issuer, wrong-audience, 401, and 403 cases.",
    "7. Use HTTPS and approved secret management for network deployment.",
    "",
    "SAFETY",
    "No application source files were changed by this validation script.",
    "No packages were installed. No server was started. No identity provider was contacted.",
    "Static checks do not prove runtime security or real authentication.",
    "",
    f"Static checks passed: {sum(1 for _, passed, _ in results if passed)}/{len(results)}",
    f"Static checks failed: {sum(1 for _, passed, _ in results if not passed)}",
]
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nREPORT_PATH={REPORT}")
sys.exit(0 if all(passed for _, passed, _ in results) else 2)
