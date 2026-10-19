from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from app import case_store
from app.case_repository import connect, update_case
from app.case_store import list_demo_cases
from app.auth_dependencies import require_permission

app = FastAPI(
    title="CIRT DFIR Platform API",
    version="0.1.0",
    description="Development scaffold only. Synthetic data; no evidence intake.",
)


class HealthResponse(BaseModel):
    status: str
    mode: str




class CaseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    severity: str | None = None

class DemoCase(BaseModel):
    case_id: str
    title: str
    severity: str
    status: str


DEMO_CASES = [
    DemoCase(
        case_id="DEMO-2026-001",
        title="Endpoint Alert Review",
        severity="High",
        status="Investigating",
    ),
    DemoCase(
        case_id="DEMO-2026-002",
        title="Suspicious Login Review",
        severity="Medium",
        status="Triage",
    ),
    DemoCase(
        case_id="DEMO-2026-003",
        title="Mailbox Rule Assessment",
        severity="Medium",
        status="Evidence review",
    ),
]


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", mode="development-scaffold")




@app.patch("/api/v1/cases/{case_id}", response_model=DemoCase, dependencies=[Depends(require_permission("cases:update"))])
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
        message = str(exc)
        if message == "Update contains no case changes.":
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=422, detail=message) from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    return DemoCase(**updated)

@app.get("/api/v1/demo/cases", response_model=list[DemoCase], dependencies=[Depends(require_permission("cases:read"))])
def get_demo_cases() -> list[DemoCase]:
    return [DemoCase(**item) for item in list_demo_cases()]
