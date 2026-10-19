import ast
import hashlib
import sys
from pathlib import Path

main_path = Path(sys.argv[1])
test_path = Path(sys.argv[2])

main_text = main_path.read_text(encoding="utf-8")
test_text = test_path.read_text(encoding="utf-8")
tree = ast.parse(main_text)
lines = main_text.splitlines()

print("=== CURRENT MAIN.PY SHA256 ===")
print(hashlib.sha256(main_text.encode("utf-8")).hexdigest())

print("\n=== CURRENT PATCH ENDPOINT ===")
found = False
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "update_case_endpoint":
        found = True
        for i in range(node.lineno - 1, node.end_lineno):
            print(f"{i+1:04d}: {lines[i]}")
if not found:
    print("Endpoint not found.")

print("\n=== NO-CHANGE TEST SOURCE ===")
test_lines = test_text.splitlines()
test_tree = ast.parse(test_text)
for node in ast.walk(test_tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "test_no_change_returns_conflict":
        for i in range(node.lineno - 1, node.end_lineno):
            print(f"{i+1:04d}: {test_lines[i]}")

print("\n=== ALL SOURCE REFERENCES TO CONFLICT MAPPING ===")
for i, line in enumerate(lines, 1):
    if "409" in line or "no case changes" in line.lower() or "ValueError" in line:
        print(f"{i:04d}: {line}")

print("\nRead-only review complete. No files modified.")