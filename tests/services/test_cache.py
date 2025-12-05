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


def test_get_all_visit_keys_success():
    """Test that get_all_visit_keys returns all keys from Redis using SCAN."""
    mock_redis = MagicMock()

    mock_redis.scan.side_effect = [
        (1, ["visits:abc", "visits:def"]),
        (0, ["visits:ghi"]),
    ]
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        keys = RedisClient.get_all_visit_keys()
    assert keys == ["visits:abc", "visits:def", "visits:ghi"]


def test_get_all_visit_keys_failure_logs_warning(caplog):
    """Test that Redis errors return empty list and log warning."""
    mock_redis = MagicMock()
    mock_redis.scan.side_effect = redis_exceptions.RedisError("fail")
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        keys = RedisClient.get_all_visit_keys()
    assert not keys
    assert any(
        "Failed to fetch visit keys" in record.message for record in caplog.records
    )


def test_get_visit_count_success():
    """Test get_visit_count returns correct integer."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = "5"
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        count = RedisClient.get_visit_count("abc")
    assert count == 5


def test_get_visit_count_none_and_failure_logs_warning(caplog):
    """Test get_visit_count returns 0 if key missing, None on Redis failure."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        count = RedisClient.get_visit_count("abc")
    assert count == 0

    mock_redis.get.side_effect = redis_exceptions.RedisError("fail")
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        count = RedisClient.get_visit_count("abc")
    assert count is None
    assert any(
        "Failed to get visit count" in record.message for record in caplog.records
    )


def test_increment_visit_count_success():
    """Test increment_visit_count increments correctly."""
    mock_redis = MagicMock()
    mock_redis.incrby.return_value = 10
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        new_count = RedisClient.increment_visit_count("abc", 3)
    assert new_count == 10
    mock_redis.incrby.assert_called_once_with("visits:abc", 3)


def test_increment_visit_count_failure_logs_warning(caplog):
    """Test increment_visit_count handles RedisError and logs warning."""
    mock_redis = MagicMock()
    mock_redis.incrby.side_effect = redis_exceptions.RedisError("fail")
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        result = RedisClient.increment_visit_count("abc", 3)
    assert result is None
    assert any(
        "Failed to increment visit count" in record.message for record in caplog.records
    )


def test_decrement_visit_count_success_and_deletes_key():
    """Test decrement_visit_count decrements and deletes key if zero."""
    mock_redis = MagicMock()
    mock_redis.decrby.return_value = 0
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        result = RedisClient.decrement_visit_count("abc", 5)
    assert result == 0
    mock_redis.delete.assert_called_once_with("visits:abc")


def test_decrement_visit_count_failure_logs_warning(caplog):
    """Test decrement_visit_count handles RedisError and logs warning."""
    mock_redis = MagicMock()
    mock_redis.decrby.side_effect = redis_exceptions.RedisError("fail")
    with patch.object(RedisClient, "get_client", return_value=mock_redis):
        result = RedisClient.decrement_visit_count("abc", 2)
    assert result is None
    assert any(
        "Failed to decrement visit count" in record.message for record in caplog.records
    )
