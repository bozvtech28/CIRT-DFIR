from pathlib import Path
import re

root = Path.cwd()
project = root.parent.parent

targets = [
    root / "app" / "main.py",
    root / "app" / "auth_dependencies.py",
    root / "app" / "entra_config_preflight.py",
    root / "app" / "entra_authenticator.py",
    root / "requirements.txt",
    project / ".gitignore",
    project / "README.md",
]

pattern = re.compile(
    r"CIRT_DFIR_ENTRA_|load_dotenv|dotenv_values|"
    r"BaseSettings|pydantic_settings|env_file|"
    r"os\.environ|os\.getenv|EnvironmentFile|"
    r"python-dotenv|uvicorn|\.env|fail.closed|"
    r"NOT wired into FastAPI|create_entra_authenticator",
    re.IGNORECASE,
)

print("CIRT-DFIR - PHASE 8B183")
print("Targeted application configuration source review")
print("Read-only; excludes virtual environments and historical reports.")
print()

for path in targets:
    print("=" * 76)
    print("FILE:", path)
    print("=" * 76)

    if not path.is_file():
        print("MISSING")
        print()
        continue

    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    matches = [
        (n, line.strip()[:240])
        for n, line in enumerate(lines, 1)
        if pattern.search(line)
    ]

    if matches:
        for number, line in matches[:80]:
            print(f"{number}: {line}")
        if len(matches) > 80:
            print("Additional matches omitted:", len(matches) - 80)
    else:
        print("No selected configuration markers found.")

    print("Total lines:", len(lines))
    print()

print("=" * 76)
print("REVIEW CONCLUSION")
print("=" * 76)
print("Marker results require manual interpretation.")
print("No environment values or credentials were printed.")
print("No source, configuration, or environment variables were changed.")
print("Authentication must remain fail-closed pending approved configuration.")
print("STATUS: REVIEW ONLY")
