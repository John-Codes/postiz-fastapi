from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_works_without_postiz_configured(client: TestClient) -> None:
    """The point of /health: it must not depend on Postiz at all."""
    assert client.get("/health").status_code == 200
