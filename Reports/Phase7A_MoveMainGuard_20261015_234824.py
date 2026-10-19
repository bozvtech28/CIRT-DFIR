import sys
from pathlib import Path

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
guard = 'if __name__ == "__main__":'

if text.count(guard) != 1:
    raise SystemExit("STOP: expected exactly one main guard; file unchanged.")

lines = text.splitlines()
guard_index = next(i for i, line in enumerate(lines) if line == guard)
if guard_index >= 106:
    raise SystemExit("STOP: main guard is not in the expected early position; file unchanged.")

# Remove the existing main guard and its unittest.main() call.
del lines[guard_index:guard_index + 2]

# Remove excess trailing blank lines and append the main guard after all tests.
while lines and not lines[-1].strip():
    lines.pop()

lines.extend(["", "", 'if __name__ == "__main__":', "    unittest.main(verbosity=2)", ""])
updated = "\n".join(lines)

# Validate syntax and expected method layout before writing.
compile(updated, str(p), "exec")
expected = [
    "test_update_case_records_before_and_after_audit",
    "test_update_missing_case_returns_none",
    "test_update_rejects_invalid_status",
    "test_update_rejects_empty_actor",
    "test_update_rejects_no_change",
]
for name in expected:
    if updated.count("def " + name + "(") != 1:
        raise SystemExit(f"STOP: expected exactly one definition of {name}; file unchanged.")

if updated.index(guard) < max(updated.index("def " + name + "(") for name in expected):
    raise SystemExit("STOP: main guard still precedes lifecycle tests; file unchanged.")

p.write_text(updated, encoding="utf-8", newline="\n")
print("PASS: moved main guard to end of test file.")
print("PASS: Python syntax validated.")
print("PASS: all five lifecycle test definitions retained.")