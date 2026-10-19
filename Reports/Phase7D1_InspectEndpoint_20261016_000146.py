import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
tree = ast.parse(text)
lines = text.splitlines()

print("=== IMPORTS AND MODELS ===")
for i, line in enumerate(lines, 1):
    if i <= 100:
        print(f"{i:04d}: {line}")

print("\n=== PATCH ROUTES AND EXCEPTION HANDLING ===")
found = False
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        decorators = [
            ast.unparse(d) for d in node.decorator_list
        ]
        if any(".patch(" in d or "update_case_endpoint" in d for d in decorators) or node.name == "update_case_endpoint":
            found = True
            start = max(0, node.lineno - 1)
            end = min(len(lines), node.end_lineno)
            print(f"\n--- Function: {node.name}, lines {node.lineno}-{node.end_lineno} ---")
            for idx in range(start, end):
                print(f"{idx+1:04d}: {lines[idx]}")

if not found:
    print("No PATCH endpoint function found by AST inspection.")

print("\n=== NO-CHANGE ERROR STRING REFERENCES ===")
for i, line in enumerate(lines, 1):
    if "no case changes" in line.lower() or "HTTPException" in line or "ValueError" in line:
        print(f"{i:04d}: {line}")

print("\nREAD-ONLY inspection complete. No files modified.")