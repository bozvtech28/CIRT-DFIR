import importlib.metadata
import importlib.util
from pathlib import Path

requirements = Path("requirements.txt")
text = requirements.read_text(encoding="utf-8-sig")
active_lines = [
    line.strip()
    for line in text.splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]

print("REQUIREMENTS_FILE:", requirements.resolve())
print("FASTAPI_DECLARED:", any(x.lower().startswith("fastapi") for x in active_lines))
print("CRYPTOGRAPHY_DECLARED:", any(x.lower().startswith("cryptography") for x in active_lines))

for module in ("cryptography", "jwt", "jose", "fastapi", "pytest"):
    try:
        available = importlib.util.find_spec(module) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        available = False
    print(f"MODULE_AVAILABLE_{module.upper()}:", available)

for package in ("cryptography", "PyJWT", "python-jose", "fastapi", "pytest"):
    try:
        version = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        version = "NOT INSTALLED"
    print(f"PACKAGE_VERSION_{package}:", version)
