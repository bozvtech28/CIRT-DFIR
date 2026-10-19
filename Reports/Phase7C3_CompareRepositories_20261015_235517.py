import ast
import hashlib
import sys
from pathlib import Path

design = Path(sys.argv[1])
backend = Path(sys.argv[2])

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def functions(path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

print("DESIGN SHA256 :", digest(design))
print("BACKEND SHA256:", digest(backend))

d = functions(design)
b = functions(backend)

print("\n=== FUNCTION INVENTORY ===")
print("Design :", ", ".join(sorted(d)))
print("Backend:", ", ".join(sorted(b)))

print("\n=== FUNCTION-BY-FUNCTION COMPARISON ===")
for name in sorted(set(d) | set(b)):
    if name not in d:
        print(f"BACKEND ONLY | {name}")
    elif name not in b:
        print(f"DESIGN ONLY  | {name}")
    elif d[name] == b[name]:
        print(f"MATCH        | {name}")
    else:
        print(f"DIFFERENT    | {name}")

print("\n=== IMPORTS AND CONSTANTS COMPARISON ===")
def non_functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        ast.dump(node, include_attributes=False)
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

print("Non-function module sections match:",
      non_functions(design) == non_functions(backend))

print("\n=== BACKEND update_case LOCATION ===")
text = backend.read_text(encoding="utf-8").splitlines()
for i, line in enumerate(text):
    if line.startswith("def update_case("):
        start = max(0, i - 3)
        end = min(len(text), i + 12)
        for j in range(start, end):
            print(f"{j+1:04d}: {text[j]}")
        break
else:
    print("update_case() NOT FOUND")

print("\nREAD-ONLY COMPARISON COMPLETE.")