import ast
from pathlib import Path
import sys

root = Path(r"C:\Users\BOZVLENOVO7\Desktop\PROJECT\CIRT_DFIR_Professional")
main_path = root / "platform/backend/app/main.py"
text = main_path.read_text(encoding="utf-8-sig")
original = text

# Ensure the FastAPI Depends symbol is imported.
if "from fastapi import " in text:
    lines = text.splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith("from fastapi import ") and "Depends" not in line:
            lines[i] = line.rstrip() + ", Depends"
            found = True
            break
        if line.startswith("from fastapi import ") and "Depends" in line:
            found = True
            break
    if not found:
        raise RuntimeError("Could not safely locate the FastAPI import.")
    text = "\n".join(lines) + ("\n" if original.endswith("\n") else "")
else:
    raise RuntimeError("Expected a from fastapi import statement; no changes applied.")

auth_import = "from app.auth_dependencies import require_permission"
if auth_import not in text:
    lines = text.splitlines()
    # Insert after the import block at the top of the module.
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            insert_at = i + 1
    lines.insert(insert_at, auth_import)
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

tree = ast.parse(text)
wanted = {
    "update_case_endpoint": "cases:update",
    "get_demo_cases": "cases:read",
}
insertions = []

for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    if node.name not in wanted:
        continue

    matches = []
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
            continue
        if not isinstance(dec.func.value, ast.Name) or dec.func.value.id != "app":
            continue
        method = dec.func.attr.lower()
        if node.name == "update_case_endpoint" and method == "patch":
            matches.append(dec)
        elif node.name == "get_demo_cases" and method == "get":
            matches.append(dec)

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one matching route decorator for {node.name}; found {len(matches)}."
        )

    dec = matches[0]
    # Avoid adding the same dependency twice if the command is rerun.
    segment = ast.get_source_segment(text, dec) or ""
    if "require_permission" in segment:
        continue

    end_line = dec.end_lineno
    end_col = dec.end_col_offset
    source_lines = text.splitlines(keepends=True)
    line_index = end_line - 1
    absolute = sum(len(line) for line in source_lines[:line_index]) + end_col
    if absolute <= 0 or text[absolute - 1] != ")":
        raise RuntimeError(f"Could not safely locate the end of {node.name}'s route decorator.")

    permission = wanted[node.name]
    insertion = f', dependencies=[Depends(require_permission("{permission}"))]'
    insertions.append((absolute - 1, insertion))

for position, insertion in sorted(insertions, reverse=True):
    text = text[:position] + insertion + text[position:]

# Confirm that both protected routes have the intended policy before writing.
check = ast.parse(text)
confirmed = set()
for node in ast.walk(check):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                seg = ast.get_source_segment(text, dec) or ""
                if "require_permission" in seg:
                    confirmed.add(node.name)

if not {"update_case_endpoint", "get_demo_cases"}.issubset(confirmed):
    raise RuntimeError("Route protection verification failed; main.py was not written.")

if text != original:
    main_path.write_text(text, encoding="utf-8")
    print("Updated main.py with fail-closed route dependencies.")
else:
    print("main.py already has the expected route dependencies.")

auth_path = root / "platform/backend/app/auth_dependencies.py"
auth_code = '''"""Fail-closed authentication gate pending approved OIDC integration.

This module intentionally authenticates nobody. Replace the placeholder
identity provider integration only after the organization chooses a provider.
Never trust roles supplied by a browser or request body.
"""
from fastapi import Depends, HTTPException

from app.security import (
    AuthenticationRequired,
    AuthorizationDenied,
    Principal,
    authorize,
)

def get_current_principal() -> Principal:
    """Reject all requests until real token/session validation is implemented."""
    raise HTTPException(
        status_code=401,
        detail="Authentication is not configured. Access is denied by default.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_permission(permission: str):
    """Require a validated principal and enforce the RBAC permission."""
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        try:
            authorize(principal, permission)
        except AuthenticationRequired as exc:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except AuthorizationDenied as exc:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permission.",
            ) from exc
        return principal
    return dependency
'''
auth_path.write_text(auth_code, encoding="utf-8")
print("Created fail-closed auth_dependencies.py.")
