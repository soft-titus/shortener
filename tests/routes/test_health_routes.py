"""
Tests for the /health endpoint.
"""

from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.health_routes import router
from app.services.cache import RedisClient
from app.services.db import PostgresDB


app = FastAPI()
app.include_router(router)


def test_health_success():
    """Redis and Postgres healthy, 200 returned."""
    with patch.object(
        RedisClient, "check_health", return_value=None
    ) as mock_redis, patch.object(
        PostgresDB, "check_health", return_value=None
    ) as mock_pg:

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "redis": "connected",
            "postgres": "connected",
        }

        mock_redis.assert_called_once()
        mock_pg.assert_called_once()


def test_health_redis_failure():
    """Redis fails, 503 returned."""
    with patch.object(
        RedisClient, "check_health", side_effect=Exception("redis err")
    ), patch.object(PostgresDB, "check_health", return_value=None):

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"detail": "Redis: not connected"}


def test_health_postgres_failure():
    """Postgres fails, 503 returned."""
    with patch.object(RedisClient, "check_health", return_value=None), patch.object(
        PostgresDB, "check_health", side_effect=Exception("pg err")
    ):

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"detail": "Postgres: not connected"}
