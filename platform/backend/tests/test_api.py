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
