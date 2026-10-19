import sys
from pathlib import Path

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")

replacements = [
    (
        'status="Investigating",\n            severity="High",',
        'status="Evidence review",\n            severity="Critical",',
        1,
    ),
    (
        'self.assertEqual(updated["status"], "Investigating")',
        'self.assertEqual(updated["status"], "Evidence review")',
        1,
    ),
    (
        'self.assertEqual(updated["severity"], "High")',
        'self.assertEqual(updated["severity"], "Critical")',
        1,
    ),
    (
        'details["before"]["status"], "Triage"',
        'details["before"]["status"], "Investigating"',
        1,
    ),
    (
        'details["after"]["status"], "Investigating"',
        'details["after"]["status"], "Evidence review"',
        1,
    ),
]

for old, new, expected_count in replacements:
    actual = text.count(old)
    if actual != expected_count:
        raise SystemExit(
            f"STOP: expected {expected_count} occurrence(s) of {old!r}; found {actual}. File unchanged."
        )
    text = text.replace(old, new, expected_count)

# The fixture already creates High / Investigating.
# Requesting Investigating again must be a no-change update.
old_no_change = 'status="Triage",'
if text.count(old_no_change) < 1:
    raise SystemExit("STOP: no-change test status anchor not found; file unchanged.")

start = text.index("def test_update_rejects_no_change(")
end = text.find("\n    def ", start + 1)
if end == -1:
    end = text.find('\nif __name__ == "__main__":', start)
if end == -1:
    end = len(text)

block = text[start:end]
if block.count('status="Triage",') != 1:
    raise SystemExit("STOP: expected one Triage status in no-change test; file unchanged.")
block = block.replace('status="Triage",', 'status="Investigating",', 1)
text = text[:start] + block + text[end:]

compile(text, str(p), "exec")
p.write_text(text, encoding="utf-8", newline="\n")
print("PASS: update test now requests real status and severity changes.")
print("PASS: no-change test now matches the fixture's existing status.")
print("PASS: Python syntax validated.")