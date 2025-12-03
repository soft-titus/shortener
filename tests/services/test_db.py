"""
Tests for the Postgres database service (services/db.py).
"""

from unittest.mock import patch, MagicMock
import pytest
from psycopg2 import OperationalError
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
