from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "development-scaffold"


def test_demo_cases_are_synthetic() -> None:
    response = client.get("/api/v1/demo/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 3
    assert all(item["case_id"].startswith("DEMO-") for item in cases)
