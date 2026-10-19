import ast
import hashlib
import sys
from pathlib import Path

design_path = Path(sys.argv[1])
backend_path = Path(sys.argv[2])

design_text = design_path.read_text(encoding="utf-8")
backend_text = backend_path.read_text(encoding="utf-8")
design_tree = ast.parse(design_text)
backend_tree = ast.parse(backend_text)

def top_level_nodes(tree):
    return [
        node for node in tree.body
        if not (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "update_case"
        )
    ]

# Only proceed if all existing top-level code matches, ignoring update_case().
design_base = top_level_nodes(design_tree)
backend_base = top_level_nodes(backend_tree)

design_dump = [ast.dump(node, include_attributes=False) for node in design_base]
backend_dump = [ast.dump(node, include_attributes=False) for node in backend_base]

if design_dump != backend_dump:
    print("STOP: Existing repository code differs beyond update_case().")
    print("No backend source was changed.")
    raise SystemExit(2)

if any(
    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "update_case"
    for node in backend_tree.body
):
    print("STOP: Backend already contains update_case(); no change made.")
    raise SystemExit(3)

source_lines = design_text.splitlines(keepends=True)
update_node = next(
    node for node in design_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "update_case"
)
function_text = "".join(source_lines[update_node.lineno - 1:update_node.end_lineno])
function_text += "\n\n"

# Insert immediately before get_case() to preserve existing module structure.
backend_lines = backend_text.splitlines(keepends=True)
backend_get_case = next(
    (node for node in backend_tree.body
     if isinstance(node, ast.FunctionDef) and node.name == "get_case"),
    None,
)
if backend_get_case is None:
    print("STOP: get_case() anchor not found. No backend source was changed.")
    raise SystemExit(4)

insert_at = backend_get_case.lineno - 1
updated = "".join(backend_lines[:insert_at]) + function_text + "".join(backend_lines[insert_at:])

# Validate syntax and ensure all original backend top-level nodes remain unchanged.
updated_tree = ast.parse(updated)
if not any(
    isinstance(node, ast.FunctionDef) and node.name == "update_case"
    for node in updated_tree.body
):
    raise SystemExit("STOP: update_case() missing after patch; no write performed.")

updated_base = [
    node for node in updated_tree.body
    if not (isinstance(node, ast.FunctionDef) and node.name == "update_case")
]
if [ast.dump(n, include_attributes=False) for n in updated_base] != backend_dump:
    raise SystemExit("STOP: Existing code would change; no write performed.")

backend_path.write_text(updated, encoding="utf-8", newline="\n")
print("PASS: Existing repository code matched before synchronization.")
print("PASS: Added only update_case() from the validated design copy.")
print("PASS: Updated backend Python syntax is valid.")
print("SHA256 after update:", hashlib.sha256(backend_path.read_bytes()).hexdigest())