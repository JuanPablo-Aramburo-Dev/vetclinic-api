"""Tests for the system endpoints (/health and /)."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_returns_200(self, client: TestClient) -> None:
        """Health endpoint should respond with 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_json_with_status_ok(self, client: TestClient) -> None:
        """Health endpoint should return status='ok' in JSON body."""
        response = client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    def test_returns_service_name(self, client: TestClient) -> None:
        """Health endpoint should include the service name."""
        response = client.get("/health")
        body = response.json()
        assert "service" in body
        assert isinstance(body["service"], str)


class TestRootEndpoint:
    """Tests for GET /."""

    def test_returns_200(self, client: TestClient) -> None:
        """Root endpoint should respond with 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_metadata(self, client: TestClient) -> None:
        """Root endpoint should return name, version, and docs URL."""
        response = client.get("/")
        body = response.json()
        assert "name" in body
        assert "version" in body
        assert body["docs"] == "/docs"
