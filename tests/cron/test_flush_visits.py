"""
Tests for app.cron.flush_visits.
"""

from unittest.mock import patch

from psycopg2 import OperationalError

from app.cron import flush_visits


def test_extract_short_code_valid() -> None:
    """Test valid Redis key extraction."""
    key = "visits:abc123"
    result = flush_visits.extract_short_code(key)
    assert result == "abc123"


def test_extract_short_code_invalid() -> None:
    """Test invalid Redis key returns None."""
    assert flush_visits.extract_short_code("invalid:key") is None
    assert flush_visits.extract_short_code("visits:") is None


@patch("app.cron.flush_visits.RedisClient.get_all_visit_keys", return_value=[])
@patch("app.cron.flush_visits.RedisClient.get_visit_count")
@patch("app.cron.flush_visits.PostgresDB.increment_visits_bulk")
@patch("app.cron.flush_visits.RedisClient.decrement_visit_count")
def test_main_no_keys(
    mock_decrement, mock_increment_bulk, mock_get_count, mock_get_keys
) -> None:
    """Test main when no keys in Redis."""
    flush_visits.main()
    mock_get_keys.assert_called_once()
    mock_get_count.assert_not_called()
    mock_increment_bulk.assert_not_called()
    mock_decrement.assert_not_called()


@patch(
    "app.cron.flush_visits.RedisClient.get_all_visit_keys",
    return_value=["visits:abc123"],
)
@patch("app.cron.flush_visits.RedisClient.get_visit_count", return_value=5)
@patch("app.cron.flush_visits.PostgresDB.increment_visits_bulk")
@patch("app.cron.flush_visits.RedisClient.decrement_visit_count", return_value=0)
def test_main_flush_success(
    mock_decrement,
    mock_increment_bulk,
    mock_get_count,
    mock_get_keys,
) -> None:
    """Test main successfully flushes visits to Postgres."""
    flush_visits.main()
    mock_get_keys.assert_called_once()
    mock_get_count.assert_called_once_with("abc123")
    mock_increment_bulk.assert_called_once_with({"abc123": 5})
    mock_decrement.assert_called_once_with("abc123", 5)


@patch(
    "app.cron.flush_visits.RedisClient.get_all_visit_keys",
    return_value=["visits:abc123", "visits:def456", "visits:ghi789"],
)
@patch(
    "app.cron.flush_visits.RedisClient.get_visit_count",
    side_effect=[5, 3, 0],  # last key has 0 visits and should be skipped
)
@patch("app.cron.flush_visits.PostgresDB.increment_visits_bulk")
@patch(
    "app.cron.flush_visits.RedisClient.decrement_visit_count",
    side_effect=[0, 0],  # only two keys with counts >0
)
def test_main_flush_multiple_keys(
    mock_decrement,
    mock_increment_bulk,
    mock_get_count,
    mock_get_keys,
) -> None:
    """Test main flush with multiple Redis keys."""
    flush_visits.main()

    mock_get_keys.assert_called_once()
    assert mock_get_count.call_count == 3
    mock_get_count.assert_any_call("abc123")
    mock_get_count.assert_any_call("def456")
    mock_get_count.assert_any_call("ghi789")
    mock_increment_bulk.assert_called_once_with({"abc123": 5, "def456": 3})
    assert mock_decrement.call_count == 2
    mock_decrement.assert_any_call("abc123", 5)
    mock_decrement.assert_any_call("def456", 3)


@patch(
    "app.cron.flush_visits.RedisClient.get_all_visit_keys",
    return_value=["visits:"],
)
@patch("app.cron.flush_visits.RedisClient.get_visit_count")
@patch("app.cron.flush_visits.PostgresDB.increment_visits_bulk")
@patch("app.cron.flush_visits.RedisClient.decrement_visit_count")
def test_main_flush_invalid_keys(
    mock_decrement,
    mock_increment_bulk,
    mock_get_count,
    mock_get_keys,
) -> None:
    """Test main flush with invalid redis key."""
    flush_visits.main()

    mock_get_keys.assert_called_once()
    mock_get_count.assert_not_called()
    mock_increment_bulk.assert_not_called()
    mock_decrement.assert_not_called()


@patch(
    "app.cron.flush_visits.RedisClient.get_all_visit_keys",
    return_value=["visits:abc123"],
)
@patch("app.cron.flush_visits.RedisClient.get_visit_count", return_value=None)
@patch("app.cron.flush_visits.PostgresDB.increment_visits_bulk")
@patch("app.cron.flush_visits.RedisClient.decrement_visit_count")
def test_main_flush_get_visit_count_failed(
    mock_decrement,
    mock_increment_bulk,
    mock_get_count,
    mock_get_keys,
) -> None:
    """Test main flush with get_visit_count failed."""
    flush_visits.main()

    mock_get_keys.assert_called_once()
    mock_get_count.assert_called_with("abc123")
    mock_increment_bulk.assert_not_called()
    mock_decrement.assert_not_called()


@patch(
    "app.cron.flush_visits.RedisClient.get_all_visit_keys",
    return_value=["visits:abc123"],
)
@patch("app.cron.flush_visits.RedisClient.get_visit_count", return_value=5)
@patch(
    "app.cron.flush_visits.PostgresDB.increment_visits_bulk",
    side_effect=OperationalError("DB fail"),
)
@patch("app.cron.flush_visits.RedisClient.decrement_visit_count")
def test_main_increment_bulk_operational_error(
    mock_decrement,
    mock_increment_bulk,
    mock_get_count,
    mock_get_keys,
) -> None:
    """Test main handles OperationalError from increment_visits_bulk gracefully."""
    flush_visits.main()

    mock_get_keys.assert_called_once()
    mock_get_count.assert_called_once_with("abc123")
    mock_increment_bulk.assert_called_once_with({"abc123": 5})
    mock_decrement.assert_not_called()


@patch(
    "app.cron.flush_visits.RedisClient.get_all_visit_keys",
    return_value=["visits:abc123"],
)
@patch("app.cron.flush_visits.RedisClient.get_visit_count", return_value=5)
@patch("app.cron.flush_visits.PostgresDB.increment_visits_bulk")
@patch("app.cron.flush_visits.RedisClient.decrement_visit_count", return_value=None)
def test_main_decrement_visit_count_failed(
    mock_decrement,
    mock_increment_bulk,
    mock_get_count,
    mock_get_keys,
) -> None:
    """Test main handles OperationalError from increment_visits_bulk gracefully."""
    flush_visits.main()

    mock_get_keys.assert_called_once()
    mock_get_count.assert_called_once_with("abc123")
    mock_increment_bulk.assert_called_once_with({"abc123": 5})
    mock_decrement.assert_called_once_with("abc123", 5)
