from unittest.mock import patch

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "OVERCLOCK API"
    assert data["status"] == "online"


def test_liveness_endpoint(client: TestClient):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp_utc" in data
    assert data["version"] == "0.1.0"


def test_readiness_endpoint_healthy(client: TestClient):
    with patch("app.api.v1.health.check_db_connection", return_value=True):
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["database"] == "connected"


def test_readiness_endpoint_degraded(client: TestClient):
    with patch("app.api.v1.health.check_db_connection", return_value=False):
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["dependencies"]["database"] == "unreachable"
