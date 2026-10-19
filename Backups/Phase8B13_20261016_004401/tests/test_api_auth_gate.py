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
