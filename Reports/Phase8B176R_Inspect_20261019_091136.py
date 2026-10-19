from pathlib import Path
import re
import sys

root = Path.cwd()

targets = [
    Path("app/main.py"),
    Path("app/auth_dependencies.py"),
    Path("app/security.py"),
    Path("app/entra_bearer_adapter.py"),
    Path("app/entra_authenticator.py"),
    Path("app/entra_token_verifier.py"),
    Path("app/entra_principal.py"),
]

pattern = re.compile(
    r"get_current_principal|require_permission|authorize\(|"
    r"entra_bearer_adapter|entra_authenticator|entra_token_verifier|"
    r"Depends\(|Security\(|include_router|"
    r"HTTPBearer|OAuth2PasswordBearer",
    re.IGNORECASE,
)

print("CIRT-DFIR - PHASE 8B176-R")
print("Authentication wiring boundary review")
print("READ-ONLY: source files will not be modified")
print("Working directory:", root)
print()

missing = []

for rel in targets:
    path = root / rel
    print("=== {} ===".format(rel.as_posix()))

    if not path.is_file():
        print("FILE NOT FOUND")
        missing.append(rel.as_posix())
        print()
        continue

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except Exception as exc:
        print("READ ERROR: {}: {}".format(type(exc).__name__, exc))
        print()
        continue

    matches = [
        (number, line.rstrip())
        for number, line in enumerate(lines, start=1)
        if pattern.search(line)
    ]

    if not matches:
        print("No matching wiring markers found.")
    else:
        for number, line in matches[:100]:
            print("{}: {}".format(number, line[:300]))
        if len(matches) > 100:
            print("Additional matching lines omitted:", len(matches) - 100)

    print()

print("Missing target files:", missing if missing else "None")
print("Review limitation: text matches do not prove runtime behavior.")
print("Authentication must remain fail-closed pending review and approval.")

if missing:
    print("INSPECTION STATUS: INCOMPLETE - one or more target files are missing")
    sys.exit(2)

print("INSPECTION STATUS: COMPLETED - source markers collected")
