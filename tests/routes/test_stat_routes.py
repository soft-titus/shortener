"""
Tests for the /stat endpoint.
"""

from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient
from psycopg2 import OperationalError

from app.main import app

client = TestClient(app)


def test_get_stat_success():
    """GET /stat/{code} returns 200 with correct stat payload."""
    mock_result = {
        "short_code": "abc123",
        "original_url": "https://example.com",
        "visits": 42,
        "created_at": datetime(2025, 1, 1, 12, 34, 56),
    }

    with patch(
        "app.routes.stat_routes.PostgresDB.get_short_url_stat",
        return_value=mock_result,
    ):
        response = client.get("/stat/abc123")

    assert response.status_code == 200
    assert response.json() == {
        "short_code": "abc123",
        "original_url": "https://example.com/",
        "visits": 42,
        "created": "2025-01-01T12:34:56",
    }


def test_get_stat_not_found():
    """GET /stat/{code} returns 404 when short code does not exist."""
    with patch(
        "app.routes.stat_routes.PostgresDB.get_short_url_stat",
        return_value=None,
    ):
        response = client.get("/stat/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "Short code not found"}


def test_get_stat_db_unavailable():
    """GET /stat/{code} returns 503 when database is unavailable."""
    with patch(
        "app.routes.stat_routes.PostgresDB.get_short_url_stat",
        side_effect=OperationalError("DB down"),
    ):
        response = client.get("/stat/abc123")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}
