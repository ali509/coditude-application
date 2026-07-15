from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "coditude-backend"


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "coditude-backend",
    }


def test_message() -> None:
    response = client.get("/api/v1/message")

    assert response.status_code == 200
    assert response.json()["environment"] == "local"