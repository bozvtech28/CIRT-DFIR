from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.metadata as metadata
import os
import re
import sys

ROOT = Path(r"C:\Users\BOZVLENOVO7\Desktop\PROJECT\CIRT_DFIR_Professional")
REPORT_DIR = ROOT / "Reports"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = REPORT_DIR / f"Phase8B4_IdentityDiscovery_{STAMP}.txt"

TARGETS = [
    "platform/backend/app/main.py",
    "platform/backend/app/security.py",
    "platform/backend/app/case_store.py",
    "platform/backend/requirements.txt",
    "platform/backend/tests/test_security.py",
    "platform/frontend/package.json",
    "platform/frontend/vite.config.ts",
    "README.md",
    "docs/Architecture.md",
    "docs/Requirements.md",
]

lines = []
def log(value=""):
    lines.append(str(value))

def heading(value):
    log("")
    log("=" * 72)
    log(value)
    log("=" * 72)

log("CIRT DFIR PROFESSIONAL — PHASE 8B.4")
log("Identity Provider Discovery and Security Readiness")
log(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}")
log("Read-only inspection. No secrets or environment-variable values are printed.")
log("")

contents = {}
for rel in TARGETS:
    path = ROOT / rel
    if path.is_file():
        try:
            contents[rel] = path.read_text(encoding="utf-8-sig", errors="replace")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            log(f"FOUND | {rel} | SHA256={digest}")
        except OSError as exc:
            log(f"READ ERROR | {rel} | {exc}")
    else:
        log(f"MISSING | {rel}")

heading("1. CURRENT API AND RBAC STATUS")
main_text = contents.get("platform/backend/app/main.py", "")
security_text = contents.get("platform/backend/app/security.py", "")
requirements = contents.get("platform/backend/requirements.txt", "")
routes = []

if main_text:
    try:
        tree = ast.parse(main_text)
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
                routes.append((dec.func.attr.upper(), path, node.name, node.lineno))
        for method, path, function, lineno in sorted(routes, key=lambda r: r[3]):
            log(f"ROUTE | {method} {path} | handler={function} | line={lineno}")
    except SyntaxError as exc:
        log(f"API SOURCE PARSE ERROR: {exc}")

log(f"RBAC module found: {bool(security_text.strip())}")
log(f"RBAC permission definitions found: {'PERMISSIONS' in security_text}")
log(f"OIDC token validation references in RBAC module: {bool(re.search(r'jwt|jwks|openid|issuer|audience|token.*valid', security_text, re.I))}")
log("Note: RBAC policy code alone does not establish user identity.")

heading("2. IDENTITY PROVIDER CONFIGURATION MARKERS")
combined = "\n".join(contents.values())
markers = [
    ("Microsoft Entra / Azure AD", r"\b(ENTRA|AZURE_AD|AZUREAD|TENANT_ID|MSAL|Microsoft.Identity)\b"),
    ("OIDC issuer / discovery", r"\b(oidc|openid|issuer|discovery|well-known/openid-configuration)\b"),
    ("OAuth client configuration", r"\b(client_id|client_secret|redirect_uri|callback_url|authority_url)\b"),
    ("Keycloak", r"\b(KEYCLOAK|keycloak)\b"),
    ("OIDC/JWT library references", r"\b(authlib|PyJWT|python-jose|jwks|jwt\.decode|OAuth2AuthorizationCodeBearer)\b"),
]
for label, pattern in markers:
    found = sorted(set(re.findall(pattern, combined, re.I)), key=str.lower)
    log(f"{label}: {'matching markers found (' + ', '.join(found[:10]) + ')' if found else 'no markers found'}")

heading("3. SAFE ENVIRONMENT CONFIGURATION CHECK")
# Only report variable NAMES that are present, never their values.
candidate_names = [
    "OIDC_ISSUER_URL", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET",
    "OIDC_REDIRECT_URI", "OIDC_AUDIENCE", "OIDC_SCOPES",
    "ENTRA_TENANT_ID", "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET",
    "KEYCLOAK_URL", "KEYCLOAK_REALM", "KEYCLOAK_CLIENT_ID",
]
for name in candidate_names:
    log(f"{name}: {'SET (value withheld)' if os.environ.get(name) else 'not set in this shell'}")
log("Environment values are intentionally withheld.")
log("No .env file contents or credential values were read or printed.")

heading("4. DEPENDENCY READINESS")
installed = {}
for dist in metadata.distributions():
    name = dist.metadata.get("Name")
    if name:
        installed[name.lower().replace("_", "-")] = dist.version

for package in ["fastapi", "pydantic", "uvicorn", "pytest", "authlib", "PyJWT", "python-jose", "cryptography", "httpx"]:
    key = package.lower().replace("_", "-")
    log(f"Installed {package}: {installed.get(key, 'NOT INSTALLED')}")

log("Declared requirements:")
for raw in requirements.splitlines():
    value = raw.strip()
    if value and not value.startswith("#"):
        log(f"  {value}")

heading("5. OIDC CONFIGURATION REQUIREMENTS")
for item in [
    "Choose one approved identity provider and obtain its official issuer/discovery URL.",
    "Register a confidential server-side web application or appropriate API client with the provider.",
    "Register exact redirect URIs for the actual deployment; do not use broad wildcard redirects.",
    "Validate token signature using provider metadata/JWKS, issuer, audience, expiry, and permitted algorithms.",
    "Map roles only from trusted, validated claims or a server-controlled role store.",
    "Keep client secrets in an approved secret store or protected environment configuration, never source code.",
    "Use HTTPS for non-local deployments and secure session/cookie settings where applicable.",
    "Enforce RBAC inside every protected API endpoint and test denied requests.",
]:
    log(f"- {item}")

heading("6. SAFETY AND NEXT GATE")
log("No source files were changed.")
log("No packages were installed.")
log("No server was started and no network requests were made.")
log("No database, collector, or evidence files were accessed.")
log("This discovery report does not authenticate users and does not activate the RBAC policy.")
log("Next gate: choose and configure the actual identity provider before implementation.")

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nREPORT_PATH={REPORT}")
