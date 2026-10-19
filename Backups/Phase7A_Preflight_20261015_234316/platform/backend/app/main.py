from fastapi import FastAPI
from pydantic import BaseModel
from app.case_store import list_demo_cases

app = FastAPI(
    title="CIRT DFIR Platform API",
    version="0.1.0",
    description="Development scaffold only. Synthetic data; no evidence intake.",
)


class HealthResponse(BaseModel):
    status: str
    mode: str


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


@app.get("/api/v1/demo/cases", response_model=list[DemoCase])
def get_demo_cases() -> list[DemoCase]:
    return [DemoCase(**item) for item in list_demo_cases()]
