import ast
import sys
from pathlib import Path

for filename in sys.argv[1:]:
    path = Path(filename)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    print(f"\n===== {path.name} =====")
    lines = source.splitlines()

    targets = {"create_case", "setUp", "make_case"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in targets:
            print(f"\n--- {node.name} (lines {node.lineno}-{node.end_lineno}) ---")
            for number in range(node.lineno, node.end_lineno + 1):
                print(f"{number:04d}: {lines[number - 1]}")