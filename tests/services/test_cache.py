"""
Tests for the Redis cache service (services/cache.py).
"""

from unittest.mock import patch
import pytest
from redis import Redis, exceptions as redis_exceptions
from app.services.cache import RedisClient


def test_get_client_returns_instance():
    """Test that get_client returns a Redis instance."""
    client1 = RedisClient.get_client()
    client2 = RedisClient.get_client()
    assert isinstance(client1, Redis)
    assert client1 is client2


def test_check_health_success():
    """Test that check_health succeeds when Redis ping works."""
    with patch.object(Redis, "ping", return_value=True):
        RedisClient.check_health()


def test_check_health_failure():
    """Test that check_health raises when Redis ping fails."""
    with patch.object(
        Redis, "ping", side_effect=redis_exceptions.ConnectionError("Redis down")
    ):
        with pytest.raises(redis_exceptions.ConnectionError):
            RedisClient.check_health()
