from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_root_describes_development_api() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "CIRT DFIR Platform API"
    assert response.json()["mode"] == "development-scaffold"
    assert response.json()["health"] == "/api/v1/health"


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "development-scaffold"


def test_demo_cases_are_synthetic() -> None:
    from app.auth_dependencies import get_current_principal
    from app.security import Principal, ROLE_ANALYST

    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="synthetic-api-test-analyst",
        roles=frozenset({ROLE_ANALYST}),
    )
    try:
        response = client.get("/api/v1/demo/cases")
        assert response.status_code == 200
        cases = response.json()
        assert len(cases) == 3
        assert all(item["case_id"].startswith("DEMO-") for item in cases)
    finally:
        app.dependency_overrides.clear()
