from pathlib import Path
import re

root = Path.cwd()

targets = [
    Path("app/main.py"),
    Path("app/auth_dependencies.py"),
    Path("app/entra_config_preflight.py"),
    Path("app/entra_authenticator.py"),
    Path("tests/test_entra_config_preflight.py"),
    Path("tests/test_entra_authenticator.py"),
    Path("tests/test_api_auth_gate.py"),
    Path("tests/test_api_oidc_fail_closed.py"),
]

patterns = re.compile(
    r"^|", re.IGNORECASE
)
patterns = re.compile(
    r"def |class |@app\.|include_router|"
    r"get_current_principal|require_permission|authorize\(|"
    r"EntraAuthConfig|create_entra_authenticator|"
    r"CIRT_DFIR_ENTRA_|expected_issuer|expected_audience|"
    r"tenant_id|discovery_url|trusted_metadata_hosts|"
    r"allowed_jwks_hosts|approved_role_map|"
    r"401|403|fail.closed|monkeypatch|TestClient",
    re.IGNORECASE,
)

print("CIRT-DFIR - PHASE 8B179")
print("Integration readiness and configuration contract")
print("READ-ONLY SOURCE INSPECTION")
print("Backend:", root)
print()

missing = []

for rel in targets:
    path = root / rel
    print("=" * 76)
    print("FILE:", rel.as_posix())
    print("=" * 76)

    if not path.is_file():
        print("FILE NOT FOUND")
        missing.append(rel.as_posix())
        print()
        continue

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    matches = []

    for number, line in enumerate(lines, start=1):
        if patterns.search(line):
            matches.append((number, line.rstrip()))

    if not matches:
        print("No matching contract markers found.")
    else:
        for number, line in matches[:120]:
            print("{}: {}".format(number, line[:260]))
        if len(matches) > 120:
            print("Additional matches omitted:", len(matches) - 120)

    print("Total source lines:", len(lines))
    print()

print("=" * 76)
print("INSPECTION SUMMARY")
print("=" * 76)
print("Missing files:", missing if missing else "None")
print("This is a text-marker review, not proof of runtime behavior.")
print("Do not enable production authentication from this report alone.")

if missing:
    print("STATUS: INCOMPLETE")
else:
    print("STATUS: SOURCE MARKERS COLLECTED")
