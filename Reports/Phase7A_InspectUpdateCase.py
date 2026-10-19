import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
tree = ast.parse(source)

node = next(
    (n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
     and n.name == "update_case"),
    None,
)

if node is None:
    raise SystemExit("STOP: update_case() not found.")

lines = source.splitlines()
print(f"Function: update_case() | lines {node.lineno}-{node.end_lineno}")
for number in range(node.lineno, node.end_lineno + 1):
    print(f"{number:04d}: {lines[number - 1]}")