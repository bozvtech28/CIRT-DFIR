import sys
from pathlib import Path

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")

names = [
    "test_update_case_records_before_and_after_audit",
    "test_update_missing_case_returns_none",
    "test_update_rejects_invalid_status",
    "test_update_rejects_empty_actor",
    "test_update_rejects_no_change",
]

lines = text.splitlines(keepends=True)
class_line = next((i for i, line in enumerate(lines) if line.startswith("class RepositoryTests")), None)
if class_line is None:
    raise SystemExit("STOP: RepositoryTests class not found.")

found = {}
for name in names:
    matches = [i for i, line in enumerate(lines) if line.lstrip().startswith("def " + name + "(")]
    if len(matches) != 1:
        raise SystemExit(f"STOP: expected one definition for {name}; found {len(matches)}.")
    found[name] = matches[0]

# Keep the existing method bodies intact; move only the five test methods
# into the test class, using their current indentation as the source.
blocks = []
for name in names:
    start = found[name]
    if start <= class_line:
        raise SystemExit(f"STOP: unexpected method position for {name}.")
    indent = len(lines[start]) - len(lines[start].lstrip())
    if indent != 4:
        raise SystemExit(f"STOP: {name} has unexpected indentation {indent}.")

    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#"):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent and (
                line.lstrip().startswith("def ")
                or line.lstrip().startswith("class ")
            ):
                break
        end += 1

    block = lines[start:end]
    if not block:
        raise SystemExit(f"STOP: empty block for {name}.")
    blocks.append((start, end, block))

# Remove blocks from the bottom upwards to preserve offsets.
for start, end, block in sorted(blocks, reverse=True):
    del lines[start:end]

# Insert methods before the next top-level definition after the test class.
class_line = next(i for i, line in enumerate(lines) if line.startswith("class RepositoryTests"))
insert_at = len(lines)
for i in range(class_line + 1, len(lines)):
    line = lines[i]
    if line.startswith("def ") or line.startswith("class "):
        insert_at = i
        break

new_block = []
for _, _, block in blocks:
    new_block.extend(block)
    if new_block and not new_block[-1].endswith("\n"):
        new_block[-1] += "\n"
    new_block.append("\n")

lines[insert_at:insert_at] = new_block
updated = "".join(lines)

# Confirm all methods are indented inside the test class before writing.
class_line = next(i for i, line in enumerate(updated.splitlines()) if line.startswith("class RepositoryTests"))
for name in names:
    positions = [i for i, line in enumerate(updated.splitlines()) if line.lstrip().startswith("def " + name + "(")]
    if len(positions) != 1 or positions[0] <= class_line:
        raise SystemExit(f"STOP: placement verification failed for {name}.")
    method_line = updated.splitlines()[positions[0]]
    if not method_line.startswith("    def "):
        raise SystemExit(f"STOP: {name} is not a class method.")

p.write_text(updated, encoding="utf-8", newline="\n")
print("Moved the five lifecycle test methods into RepositoryTests.")