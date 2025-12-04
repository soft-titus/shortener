"""
Tests for the Redis cache service (services/cache.py).
"""

from unittest.mock import patch, MagicMock
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


def test_set_with_ttl_success():
    """Test that set_with_ttl calls Redis setex with correct arguments."""
    mock_redis = MagicMock()
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        RedisClient.set_with_ttl("mykey", "myvalue", ttl=3600)
        mock_redis.setex.assert_called_once_with(
            name="mykey", time=3600, value="myvalue"
        )


def test_set_with_ttl_uses_default_ttl(monkeypatch):
    """Test that set_with_ttl uses default TTL from CACHE_TTL env variable."""
    monkeypatch.setattr("app.config.CACHE_TTL_HOURS", 5)
    mock_redis = MagicMock()
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        RedisClient.set_with_ttl("mykey", "myvalue")
        expected_seconds = 5 * 60 * 60
        mock_redis.setex.assert_called_once_with(
            name="mykey", time=expected_seconds, value="myvalue"
        )


def test_set_with_ttl_failure_logs_warning(caplog):
    """Test that Redis errors are logged as warnings."""
    mock_redis = MagicMock()
    mock_redis.setex.side_effect = redis_exceptions.RedisError("Redis down")
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        RedisClient.set_with_ttl("mykey", "myvalue", ttl=10)
    assert any(
        "Failed to set key in Redis" in record.message for record in caplog.records
    )
