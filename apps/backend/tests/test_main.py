import pytest
from fastapi.testclient import TestClient

from app.database import database
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with TestClient(app) as test_client:
        yield test_client


def test_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "coditude-backend"


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "coditude-backend",
    }


def test_ready_returns_503_without_database(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not ready"


def test_message_uses_application_default(client: TestClient) -> None:
    response = client.get("/api/v1/message")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Backend is running successfully",
        "environment": "local",
        "source": "application-default",
    }


def test_message_uses_database_value(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        database,
        "get_message",
        lambda: "Message loaded from PostgreSQL",
    )

    response = client.get("/api/v1/message")

    assert response.status_code == 200
    assert response.json()["message"] == "Message loaded from PostgreSQL"
    assert response.json()["source"] == "postgresql"
