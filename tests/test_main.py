"""Tests for the FastAPI main application entrypoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_route_registered():
    """Verify that /health endpoint is registered in the main app."""
    response = client.get("/health")

    assert response.status_code in (200, 503)
