"""
Tests for app.services.shortener.ShortenerService.
"""

from unittest.mock import patch, MagicMock
import pytest
from redis import exceptions as redis_exceptions
from psycopg2 import OperationalError, errors

from app.services.shortener import (
    ShortenerService,
    OriginalURLAlreadyExists,
    ShortCodeGenerationFailed,
    ShortCodeNotFound,
    DatabaseUnavailable,
)


def test_shorten_url_cache_hit():
    """shorten_url raises OriginalURLAlreadyExists on cache hit."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client:
        redis_instance = MagicMock()
        redis_instance.get.return_value = "abcd1234"
        mock_client.return_value = redis_instance

        with pytest.raises(OriginalURLAlreadyExists):
            ShortenerService.shorten_url("http://example.com")


def test_shorten_url_db_exists():
    """shorten_url raises OriginalURLAlreadyExists if URL exists in DB."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.original_url_exists.return_value = True

        with pytest.raises(OriginalURLAlreadyExists):
            ShortenerService.shorten_url("http://example.com")


def test_shorten_url_unique_violation_retry():
    """shorten_url retries on UniqueViolation and succeeds."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.original_url_exists.return_value = False

        mock_db.insert_short_url.side_effect = [
            errors.UniqueViolation(  # pylint: disable=no-member
                "duplicate key value violates unique constraint"
            ),
            None,
        ]

        code = ShortenerService.shorten_url("http://example.com")
        assert isinstance(code, str)
        assert mock_db.insert_short_url.call_count == 2


def test_shorten_url_max_retries_fail():
    """shorten_url raises ShortCodeGenerationFailed after max retries."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.original_url_exists.return_value = False

        mock_db.insert_short_url.side_effect = [
            errors.UniqueViolation("duplicate")  # pylint: disable=no-member
        ] * 10

        with pytest.raises(ShortCodeGenerationFailed):
            ShortenerService.shorten_url("http://example.com")


def test_shorten_url_db_operational_error():
    """shorten_url raises DatabaseUnavailable if original_url_exists fails."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.original_url_exists.side_effect = OperationalError("DB down")

        with pytest.raises(DatabaseUnavailable):
            ShortenerService.shorten_url("http://example.com")


def test_shorten_url_insert_operational_error():
    """shorten_url raises DatabaseUnavailable if insert_short_url fails."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.original_url_exists.return_value = False
        mock_db.insert_short_url.side_effect = OperationalError("Insert failed")

        with pytest.raises(DatabaseUnavailable):
            ShortenerService.shorten_url("http://example.com")


def test_resolve_short_code_cache_hit():
    """resolve_short_code returns original URL from cache."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.RedisClient.increment_visit_count"
    ) as mock_inc:
        redis_instance = MagicMock()
        redis_instance.get.return_value = "http://example.com"
        mock_client.return_value = redis_instance

        original = ShortenerService.resolve_short_code("abcd1234")
        assert original == "http://example.com"
        mock_inc.assert_called_once_with("abcd1234")


def test_resolve_short_code_db_hit():
    """resolve_short_code returns original URL from DB if cache miss."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db, patch(
        "app.services.shortener.RedisClient.increment_visit_count"
    ) as mock_inc:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.get_original_url.return_value = "http://example.com"

        original = ShortenerService.resolve_short_code("abcd1234")
        assert original == "http://example.com"
        mock_inc.assert_called_once_with("abcd1234")


def test_resolve_short_code_not_found():
    """resolve_short_code raises ShortCodeNotFound if not in cache or DB."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.get_original_url.return_value = None

        with pytest.raises(ShortCodeNotFound):
            ShortenerService.resolve_short_code("abcd1234")


def test_resolve_short_code_db_unavailable():
    """resolve_short_code raises DatabaseUnavailable if DB is down."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.get_original_url.side_effect = OperationalError("DB down")

        with pytest.raises(DatabaseUnavailable):
            ShortenerService.resolve_short_code("abcd1234")


def test_shorten_url_redis_get_error():
    """shorten_url falls back gracefully if Redis get raises RedisError."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db, patch("app.services.shortener.RedisClient.set_with_ttl") as mock_set:

        redis_instance = MagicMock()
        redis_instance.get.side_effect = redis_exceptions.RedisError("Redis down")
        mock_client.return_value = redis_instance

        mock_db.original_url_exists.return_value = False
        mock_db.insert_short_url.return_value = None

        code = ShortenerService.shorten_url("http://example.com")
        assert isinstance(code, str)
        mock_set.assert_called()


def test_shorten_url_redis_set_error():
    """shorten_url continues if Redis set_with_ttl raises RedisError."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db, patch("app.services.shortener.RedisClient.set_with_ttl") as mock_set:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.original_url_exists.return_value = False
        mock_db.insert_short_url.return_value = None

        mock_set.side_effect = redis_exceptions.RedisError("Cannot set cache")
        code = ShortenerService.shorten_url("http://example.com")
        assert isinstance(code, str)


def test_resolve_short_code_redis_get_error_and_db_hit():
    """resolve_short_code falls back to DB and caches mapping when Redis get fails."""
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db, patch("app.services.shortener.RedisClient.set_with_ttl") as mock_set:

        redis_instance = MagicMock()
        redis_instance.get.side_effect = redis_exceptions.RedisError("Redis down")
        mock_client.return_value = redis_instance
        mock_db.get_original_url.return_value = "http://example.com"

        original = ShortenerService.resolve_short_code("abcd1234")
        assert original == "http://example.com"
        assert mock_set.call_count == 2


def test_resolve_short_code_redis_set_error_after_db():
    """
    Ensure resolve_short_code returns the URL even if Redis caching
    fails after DB fetch. Covers previously uncovered lines.
    """
    with patch("app.services.shortener.RedisClient.get_client") as mock_client, patch(
        "app.services.shortener.PostgresDB"
    ) as mock_db, patch("app.services.shortener.RedisClient.set_with_ttl") as mock_set:

        redis_instance = MagicMock()
        redis_instance.get.return_value = None
        mock_client.return_value = redis_instance
        mock_db.get_original_url.return_value = "http://example.com"

        mock_set.side_effect = redis_exceptions.RedisError("Cannot cache after DB")
        original = ShortenerService.resolve_short_code("abcd1234")

        assert original == "http://example.com"
        assert mock_set.call_count == 1
