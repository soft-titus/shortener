"""
Tests for the Postgres database service (services/db.py).
"""

from unittest.mock import patch, MagicMock
import pytest
from psycopg2 import OperationalError, errors
from app.services.db import PostgresDB


def test_get_pool_operational_error():
    """Test that get_pool logs and raises OperationalError if pool creation fails."""
    with patch(
        "app.services.db.pool.SimpleConnectionPool",
        side_effect=OperationalError("fail"),
    ):
        with pytest.raises(OperationalError, match="fail"):
            PostgresDB.get_pool()


def test_get_pool_singleton():
    """Test that get_pool returns a SimpleConnectionPool instance and is singleton."""
    mock_pool_instance = MagicMock()
    with patch(
        "app.services.db.pool.SimpleConnectionPool", return_value=mock_pool_instance
    ):
        pool1 = PostgresDB.get_pool()
        pool2 = PostgresDB.get_pool()
        assert pool1 is pool2
        assert pool1 is mock_pool_instance


def test_check_health_success():
    """Test that check_health succeeds when Postgres is reachable."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "_pool", mock_pool):
        PostgresDB.check_health()
        mock_pool.getconn.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_check_health_failure_not_initialized():
    """Test that check_health raises if pool is not initialized."""
    with patch.object(PostgresDB, "_pool", None):
        with patch.object(PostgresDB, "get_pool", return_value=None):
            with pytest.raises(OperationalError):
                PostgresDB.check_health()


def test_check_health_failure_query_error():
    """Test that check_health raises OperationalError on query failure."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = OperationalError("Query failed")
    mock_conn.cursor.return_value = mock_cursor

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "_pool", mock_pool):
        with pytest.raises(OperationalError):
            PostgresDB.check_health()


def test_original_url_exists_true():
    """Test that original_url_exists returns True when the URL is found."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = ["https://example.com"]

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        exists = PostgresDB.original_url_exists("https://example.com")
        assert exists is True
        mock_cursor.execute.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_original_url_exists_false():
    """Test that original_url_exists returns False when the URL is not found."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = None

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        exists = PostgresDB.original_url_exists("https://example.com")
        assert exists is False
        mock_cursor.execute.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_insert_short_url_success():
    """Test that insert_short_url successfully inserts a short URL and returns the short code."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = ["short123"]

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        short_code = PostgresDB.insert_short_url("short123", "https://example.com")
        assert short_code == "short123"
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_insert_short_url_unique_violation():
    """Test insert_short_url raises UniqueViolation and rolls back."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.execute.side_effect = (
        errors.UniqueViolation  # pylint: disable=no-member
    )

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        with pytest.raises(errors.UniqueViolation):  # pylint: disable=no-member
            PostgresDB.insert_short_url("short123", "https://example.com")
        mock_conn.rollback.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_insert_short_url_operational_error():
    """Test insert_short_url raises OperationalError and rolls back."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    op_err = OperationalError("DB down")
    mock_cursor.execute.side_effect = op_err

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        with pytest.raises(OperationalError):
            PostgresDB.insert_short_url("short123", "https://example.com")
        mock_conn.rollback.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_get_original_url_found():
    """Test get_original_url returns the URL when found."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = ["https://example.com"]

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        result = PostgresDB.get_original_url("short123")
        assert result == "https://example.com"
        mock_cursor.execute.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_get_original_url_not_found():
    """Test get_original_url returns None when not found."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = None

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        result = PostgresDB.get_original_url("short123")
        assert result is None
        mock_cursor.execute.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_increment_visits_bulk_success():
    """Test that increment_visits_bulk executes a bulk update and commits with correct params."""
    visit_data = {"short1": 5, "short2": 3}

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor

    def mogrify_side_effect(query, params):
        assert query == "(%s, %s)"
        assert params[0] in visit_data
        assert params[1] == visit_data[params[0]]
        return f"('{params[0]}', {params[1]})".encode("utf-8")

    mock_cursor.mogrify.side_effect = mogrify_side_effect

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        PostgresDB.increment_visits_bulk(visit_data)

        mock_cursor.execute.assert_called_once()
        executed_sql = mock_cursor.execute.call_args[0][0]
        for short_code, count in visit_data.items():
            assert short_code in executed_sql
            assert str(count) in executed_sql

        mock_conn.commit.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_increment_visits_bulk_operational_error():
    """Test that increment_visits_bulk rolls back on OperationalError."""
    visit_data = {"short1": 5, "short2": 3}

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor

    def mogrify_side_effect(_query, params):
        return f"('{params[0]}', {params[1]})".encode("utf-8")

    mock_cursor.mogrify.side_effect = mogrify_side_effect
    mock_cursor.execute.side_effect = OperationalError("DB down")

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        with pytest.raises(OperationalError):
            PostgresDB.increment_visits_bulk(visit_data)

        mock_conn.rollback.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_increment_visits_bulk_empty_dict():
    """Test that increment_visits_bulk does nothing if visit_data is empty."""
    mock_pool = MagicMock()
    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        PostgresDB.increment_visits_bulk({})
        mock_pool.getconn.assert_not_called()


def test_get_short_url_stat_found():
    """Test get_short_url_stat returns a dictionary when the short code exists."""
    mock_result = {
        "short_code": "short123",
        "original_url": "https://example.com",
        "visits": 10,
        "created_at": "2025-12-05T09:00:00",
    }

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = mock_result

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        result = PostgresDB.get_short_url_stat("short123")
        assert result == mock_result
        mock_cursor.execute.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


def test_get_short_url_stat_not_found():
    """Test get_short_url_stat returns None when the short code does not exist."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with patch.object(PostgresDB, "get_pool", return_value=mock_pool):
        result = PostgresDB.get_short_url_stat("missing")
        assert result is None
        mock_cursor.execute.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
