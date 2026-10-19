from pathlib import Path
import ast
import re

root = Path.cwd()
project = root.parent.parent

targets = {
    "auth_dependencies.py": root / "app" / "auth_dependencies.py",
    "entra_config_preflight.py": root / "app" / "entra_config_preflight.py",
    "entra_authenticator.py": root / "app" / "entra_authenticator.py",
    "entra_token_verifier.py": root / "app" / "entra_token_verifier.py",
    "entra_bearer_adapter.py": root / "app" / "entra_bearer_adapter.py",
    "main.py": root / "app" / "main.py",
    ".gitignore": project / ".gitignore",
    "README.md": project / "README.md",
}

patterns = re.compile(
    r"EntraAuthConfig|create_entra_authenticator|"
    r"tenant_id|expected_issuer|expected_audience|"
    r"discovery_url|trusted_metadata_hosts|allowed_jwks_hosts|"
    r"approved_role_map|os\.environ|os\.getenv|"
    r"load_dotenv|dotenv_values|BaseSettings|env_file|"
    r"preflight|fail.closed|NOT wired into FastAPI|"
    r"get_current_principal|require_permission|"
    r"@app\.(get|post|put|patch|delete)|"
    r"include_router|\.env",
    re.IGNORECASE,
)

print("CIRT-DFIR - PHASE 8B184")
print("Configuration contract and integration review")
print("READ ONLY - no environment values or credentials are read.")
print()

for label, path in targets.items():
    print("=" * 78)
    print(f"FILE: {label}")
    print(f"EXISTS: {path.is_file()}")
    print("=" * 78)

    if not path.is_file():
        print()
        continue

    content = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = content.splitlines()

    if path.suffix == ".py":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if (
                        node.name == "EntraAuthConfig"
                        or "entra" in node.name.lower()
                        or "preflight" in node.name.lower()
                        or node.name in ("get_current_principal", "require_permission")
                    ):
                        print(f"DECLARATION line {node.lineno}: {node.name}")
                        if isinstance(node, ast.ClassDef):
                            for child in node.body:
                                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                                    print(f"  FIELD line {child.lineno}: {child.target.id}")
                                elif isinstance(child, ast.Assign):
                                    for target in child.targets:
                                        if isinstance(target, ast.Name):
                                            print(f"  ASSIGNMENT line {child.lineno}: {target.id}")
        except SyntaxError as exc:
            print(f"AST parse error: {exc}")

    matches = [
        (number, line.strip()[:220])
        for number, line in enumerate(lines, 1)
        if patterns.search(line)
    ]

    if matches:
        for number, line in matches[:100]:
            print(f"{number}: {line}")
        if len(matches) > 100:
            print(f"Additional matches omitted: {len(matches) - 100}")
    else:
        print("No selected contract markers found.")

    print(f"TOTAL LINES: {len(lines)}")
    print()

print("=" * 78)
print("REVIEW CONCLUSION")
print("=" * 78)
print("This is a source inspection, not an authentication integration test.")
print("Do not infer that environment values are loaded merely because fields exist.")
print("Do not create production configuration from guessed tenant, issuer, audience,")
print("metadata host, JWKS host, or role-mapping values.")
print("Authentication must remain fail-closed pending approved configuration and sign-off.")
print("STATUS: REVIEW ONLY")
