from fastapi.testclient import TestClient

from app.auth_dependencies import get_current_principal
from app.main import app


client = TestClient(app)


def test_missing_bearer_token_is_rejected():
    app.dependency_overrides.clear()
    try:
        response = client.get("/api/v1/demo/cases")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_malformed_bearer_token_is_rejected():
    app.dependency_overrides.clear()
    try:
        response = client.get(
            "/api/v1/demo/cases",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_case_update_without_authentication_is_rejected():
    app.dependency_overrides.clear()
    try:
        response = client.patch(
            "/api/v1/cases/DEMO-2026-001",
            json={"status": "Contained"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
