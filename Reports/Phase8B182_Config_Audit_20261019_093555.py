import os
from pathlib import Path

root = Path.cwd()
project = root.parent.parent

print("CIRT-DFIR - PHASE 8B182")
print("Read-only deployment configuration readiness audit")
print("Backend:", root)
print()

print("=== CONFIGURATION FILE INVENTORY ===")
candidates = [
    root / ".env",
    root / ".env.example",
    root / ".env.template",
    root / ".env.sample",
    root / "requirements.txt",
    root / "pyproject.toml",
    root / "Dockerfile",
    root / "docker-compose.yml",
    root / "compose.yml",
    root / "README.md",
    project / ".env",
    project / ".env.example",
    project / ".gitignore",
    project / "README.md",
    project / "docker-compose.yml",
    project / "compose.yml",
]
seen = set()
for path in candidates:
    if path in seen:
        continue
    seen.add(path)
    print(("FOUND   " if path.is_file() else "MISSING ") + str(path))

print()
print("=== ENVIRONMENT VARIABLE STATUS ===")
for name in (
    "CIRT_DFIR_ENTRA_TENANT_ID",
    "CIRT_DFIR_ENTRA_EXPECTED_ISSUER",
    "CIRT_DFIR_ENTRA_AUDIENCE",
):
    value = os.environ.get(name)
    print(f"{name}: " + (
        "PRESENT (value hidden)" if value and value.strip()
        else "MISSING OR EMPTY"
    ))

print()
print("=== SAFE CONFIGURATION MARKERS ===")
search_roots = [root, project]
suffixes = {".py", ".toml", ".ini", ".cfg", ".md", ".yml", ".yaml", ".txt"}
needles = (
    "CIRT_DFIR_ENTRA_TENANT_ID",
    "CIRT_DFIR_ENTRA_EXPECTED_ISSUER",
    "CIRT_DFIR_ENTRA_AUDIENCE",
    "load_dotenv",
    "BaseSettings",
    "pydantic_settings",
    "env_file",
    "python-dotenv",
    "EnvironmentFile",
    "env_file:",
)
hits = 0
for base in search_roots:
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if any(part in {".venv", ".venv_phase8b166", "__pycache__", ".git", "node_modules"}
               for part in path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            if any(needle.lower() in line.lower() for needle in needles):
                print(f"{path.relative_to(base)}:{number}: {line.strip()[:200]}")
                hits += 1
                if hits >= 100:
                    print("Output capped at 100 matches.")
                    break
        if hits >= 100:
            break
    if hits >= 100:
        break
if hits == 0:
    print("No selected configuration-loading markers found.")

print()
print("=== SAFETY ===")
print("File contents and environment values were not printed.")
print("No configuration was created or modified.")
print("No network requests were made.")
print("Authentication wiring was not changed.")
print("STATUS: READ-ONLY INVENTORY; MANUAL REVIEW REQUIRED")
