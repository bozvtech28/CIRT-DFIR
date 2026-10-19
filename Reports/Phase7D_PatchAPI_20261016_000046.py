import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

if "def update_case_endpoint(" in text or '@app.patch("/api/v1/cases/{case_id}"' in text:
    print("STOP: Update endpoint already appears to exist. No change made.")
    raise SystemExit(2)

required = [
    "from fastapi import FastAPI",
    "from pydantic import BaseModel",
    "from app.case_store import list_demo_cases",
    '@app.get("/api/v1/demo/cases"',
]
missing = [item for item in required if item not in text]
if missing:
    print("STOP: Expected source structure not found:")
    for item in missing:
        print(" -", item)
    print("No change made.")
    raise SystemExit(3)

# Add imports without replacing existing imports.
text = text.replace(
    "from fastapi import FastAPI",
    "from fastapi import FastAPI, HTTPException",
    1,
)
text = text.replace(
    "from pydantic import BaseModel",
    "from pydantic import BaseModel, ConfigDict",
    1,
)
text = text.replace(
    "from app.case_store import list_demo_cases",
    "from app import case_store\nfrom app.case_repository import connect, update_case\n"
    "from app.case_store import list_demo_cases",
    1,
)

model = '''

class CaseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    severity: str | None = None

'''

if "class DemoCase(BaseModel):" not in text:
    print("STOP: DemoCase model anchor not found. No change made.")
    raise SystemExit(4)

text = text.replace(
    "class DemoCase(BaseModel):",
    model + "class DemoCase(BaseModel):",
    1,
)

route = '''

@app.patch("/api/v1/cases/{case_id}", response_model=DemoCase)
def update_case_endpoint(
    case_id: str,
    payload: CaseUpdateRequest,
) -> DemoCase:
    """Development-only case update; uses synthetic development actor."""
    if payload.status is None and payload.severity is None:
        raise HTTPException(
            status_code=422,
            detail="Provide status, severity, or both.",
        )

    try:
        case_store.ensure_database()
        db = connect(case_store.DB_PATH)
        try:
            updated = update_case(
                db,
                case_id=case_id,
                actor_id="DEVELOPMENT-API",
                timestamp=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
                status=payload.status,
                severity=payload.severity,
            )
        finally:
            db.close()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    return DemoCase(**updated)

'''

anchor = '@app.get("/api/v1/demo/cases"'
if anchor not in text:
    print("STOP: Cases GET route anchor not found. No change made.")
    raise SystemExit(5)

text = text.replace(anchor, route + anchor, 1)

# Syntax-check before writing.
ast.parse(text)
path.write_text(text, encoding="utf-8", newline="\n")
print("PASS: Added PATCH /api/v1/cases/{case_id}.")
print("PASS: Unknown request fields are forbidden.")
print("PASS: Source syntax is valid.")