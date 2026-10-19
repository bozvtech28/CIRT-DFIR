"""API access-control tests using synthetic identities only."""
from fastapi.testclient import TestClient

from app.auth_dependencies import get_current_principal
from app.main import app
from app.security import Principal, ROLE_ADMINISTRATOR, ROLE_VIEWER

client = TestClient(app)

def test_demo_cases_reject_unauthenticated_request():
    app.dependency_overrides.clear()
    try:
        response = client.get("/api/v1/demo/cases")
        assert response.status_code == 401
        assert "Authentication" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()

def test_case_update_rejects_unauthenticated_request():
    app.dependency_overrides.clear()
    try:
        response = client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"status": "Contained"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()

def test_viewer_cannot_update_case():
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="synthetic-test-viewer",
        roles=frozenset({ROLE_VIEWER}),
    )
    try:
        response = client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"status": "Contained"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

def test_case_update_audit_actor_comes_from_principal(tmp_path, monkeypatch):
    import app.case_store as case_store
    from app.case_repository import connect, initialize, create_case, list_audit_events
    from app.security import ROLE_ANALYST

    database_path = tmp_path / "audit-attribution.sqlite"
    schema_path = __import__("pathlib").Path(__file__).resolve().parents[1] / "schema.sql"
    if not schema_path.is_file():
        # Find the project's schema file without touching the configured application database.
        candidates = list(__import__("pathlib").Path(__file__).resolve().parents[1].rglob("*.sql"))
        assert candidates, "No SQL schema file found for isolated test database."
        schema_path = candidates[0]

    initialize(database_path, schema_path)
    db = connect(database_path)
    try:
        create_case(
            db,
            case_id="TEST-AUDIT-001",
            title="Synthetic audit attribution test",
            severity="Medium",
            status="Triage",
            actor_id="synthetic-test-creator",
            timestamp="2026-01-01T00:00:00+00:00",
        )
    finally:
        db.close()

    monkeypatch.setattr(case_store, "DB_PATH", database_path)
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="synthetic-audit-analyst-117",
        roles=frozenset({ROLE_ANALYST}),
    )
    try:
        response = client.patch(
            "/api/v1/cases/TEST-AUDIT-001",
            json={"status": "Contained"},
        )
        assert response.status_code == 200, response.text

        db = connect(database_path)
        try:
            events = list_audit_events(db, "TEST-AUDIT-001")
        finally:
            db.close()

        update_events = [event for event in events if event["event_type"] == "CASE_UPDATED"]
        assert len(update_events) == 1
        assert update_events[0]["actor_id"] == "synthetic-audit-analyst-117"
    finally:
        app.dependency_overrides.clear()

def test_admin_can_pass_case_update_authorization_gate():
    # Dependency override represents an already validated synthetic principal.
    # This test checks authorization only; it does not perform a database update.
    from app.auth_dependencies import require_permission
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient as LocalClient

    test_app = FastAPI()
    test_app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="synthetic-test-admin",
        roles=frozenset({ROLE_ADMINISTRATOR}),
    )

    @test_app.get("/test-protected-update-permission")
    def protected_permission_check(principal=Depends(require_permission("cases:update"))):
        return {"authorized": True}

    response = LocalClient(test_app).get("/test-protected-update-permission")
    assert response.status_code == 200
    assert response.json()["authorized"] is True

