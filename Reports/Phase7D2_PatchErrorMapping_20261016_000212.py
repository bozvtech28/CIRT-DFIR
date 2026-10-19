import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

old = '''    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
'''

new = '''    except ValueError as exc:
        message = str(exc)
        if message == "Update contains no case changes.":
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=422, detail=message) from exc
'''

if text.count(old) != 1:
    print("STOP: Expected exactly one error-mapping block; no change made.")
    raise SystemExit(2)

if "Update contains no case changes." in text:
    print("STOP: No-change mapping may already exist; no change made.")
    raise SystemExit(3)

updated = text.replace(old, new, 1)
ast.parse(updated)
path.write_text(updated, encoding="utf-8", newline="\n")

print("PASS: No-change ValueError now maps to HTTP 409.")
print("PASS: Other ValueError cases remain HTTP 422.")
print("PASS: Updated main.py syntax is valid.")