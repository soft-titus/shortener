"""
Test suite for the FastAPI in the URL Shortener app.
"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from redis import exceptions as redis_exceptions
from psycopg2 import OperationalError

from app.main import app

client = TestClient(app)


def test_health_redis_not_connected():
    """Test /health returns 503 when Redis is not reachable."""

    with patch(
        "app.main.redis_client.ping",
        side_effect=redis_exceptions.ConnectionError("Redis down"),
    ):
        response = client.get("/health")
        assert response.status_code == 503
        assert "Redis is not connected" in response.json()["detail"]


def test_health_postgres_pool_none():
    """Test /health returns 503 when Postgres not initialized."""
    with patch("app.main.redis_client.ping", return_value=True):
        with patch("app.main.pg_pool", None):
            response = client.get("/health")
            assert response.status_code == 503
            assert response.json()["detail"] == "Postgres is not connected"


def test_health_postgres_not_connected():
    """Test /health returns 503 when Postgres is not reachable."""
    with patch("app.main.redis_client.ping", return_value=True):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = OperationalError("Query failed")
        mock_conn.cursor.return_value = mock_cursor

        mock_pg_pool = MagicMock()
        mock_pg_pool.getconn.return_value = mock_conn

        with patch("app.main.pg_pool", mock_pg_pool):
            response = client.get("/health")
            assert response.status_code == 503
            assert response.json()["detail"] == "Postgres is not connected"


def test_health_ok():
    """Test /health returns 200 when Redis and Postgres is connected."""
    with patch("app.main.redis_client.ping", return_value=True):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value = mock_cursor

        mock_pg_pool = MagicMock()
        mock_pg_pool.getconn.return_value = mock_conn
        mock_pg_pool.putconn.return_value = None

        with patch("app.main.pg_pool", mock_pg_pool):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["redis"] == "connected"
            assert data["postgres"] == "connected"
