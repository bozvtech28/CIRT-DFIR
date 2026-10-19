import os
from pathlib import Path

root = Path.cwd()
required_env = [
    "CIRT_DFIR_ENTRA_TENANT_ID",
    "CIRT_DFIR_ENTRA_EXPECTED_ISSUER",
    "CIRT_DFIR_ENTRA_AUDIENCE",
]
files = [
    "app/main.py",
    "app/auth_dependencies.py",
    "app/entra_config_preflight.py",
    "app/entra_authenticator.py",
    "app/entra_bearer_adapter.py",
    "app/entra_token_verifier.py",
    "app/entra_principal.py",
    "app/entra_jwks.py",
    "app/entra_jwks_cache.py",
    "app/entra_metadata_client.py",
    "app/entra_http_transport.py",
    "app/security.py",
    "tests/test_entra_config_preflight.py",
    "tests/test_entra_authenticator.py",
    "tests/test_api_auth_gate.py",
    "tests/test_api_oidc_fail_closed.py",
]
markers = [
    "get_current_principal",
    "require_permission",
    "EntraAuthConfig",
    "create_entra_authenticator",
    "approved_role_map",
    "trusted_metadata_hosts",
    "allowed_jwks_hosts",
    "WWW-Authenticate",
    "Authentication is not configured",
    "NOT wired into FastAPI",
]

print("CIRT-DFIR - PHASE 8B180")
print("Read-only Entra integration contract and approval-gap audit")
print("Backend:", root)
print()

print("=== REQUIRED ENVIRONMENT SETTINGS ===")
for name in required_env:
    value = os.environ.get(name)
    state = "PRESENT (value intentionally not displayed)" if value and value.strip() else "MISSING OR EMPTY"
    print(f"{name}: {state}")
print()

print("=== SOURCE FILE INVENTORY ===")
missing = []
for rel in files:
    path = root / rel
    state = "FOUND" if path.is_file() else "MISSING"
    print(f"{state}: {rel}")
    if not path.is_file():
        missing.append(rel)
print()

print("=== AUTHENTICATION BOUNDARY MARKERS ===")
for rel in ("app/main.py", "app/auth_dependencies.py", "app/entra_authenticator.py",
            "app/entra_bearer_adapter.py", "app/security.py"):
    path = root / rel
    print(f"\n--- {rel} ---")
    if not path.is_file():
        print("FILE MISSING")
        continue
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    hits = 0
    for n, line in enumerate(lines, 1):
        if any(marker.lower() in line.lower() for marker in markers):
            print(f"{n}: {line.strip()[:240]}")
            hits += 1
            if hits >= 35:
                print("Further matches omitted.")
                break
    if hits == 0:
        print("No selected markers found.")
print()

print("=== APPROVAL GAPS ===")
gaps = [
    "Approved Entra tenant ID and tenant ownership",
    "Exact expected issuer validated against the selected tenant's metadata",
    "API audience / Application ID URI approved by the API owner",
    "Application roles and their mapping to internal CIRT-DFIR roles",
    "Trusted discovery metadata and JWKS host allowlists",
    "Deployment-specific secure environment configuration",
    "Security/admin approval and integration test plan",
]
for item in gaps:
    print("[ ]", item)
print()

print("=== SAFETY CONCLUSION ===")
print("Source files missing:", missing if missing else "None")
print("Environment values were not displayed.")
print("No network requests, source edits, or environment changes were performed.")
print("Do not wire Entra authentication into FastAPI until configuration and approvals are complete.")
print("STATUS: REVIEW ONLY")
