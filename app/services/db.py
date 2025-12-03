"""
database service module with Postgres.
"""

import os
import logging
from psycopg2 import pool, OperationalError

logger = logging.getLogger(__name__)


class PostgresDB:
    """
    Singleton wrapper for Postgres connection pool.
    """

    _pool: pool.SimpleConnectionPool | None = None

    @classmethod
    def get_pool(cls) -> pool.SimpleConnectionPool:
        """
        Get the Postgres connection pool instance.
        Initializes the pool if it hasn't been created yet.
        """
        if cls._pool is None:
            try:
                cls._pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=20,
                    host=os.getenv("POSTGRES_HOST", "postgres"),
                    port=int(os.getenv("POSTGRES_PORT", "5432")),
                    dbname=os.getenv("POSTGRES_DB", "shortener"),
                    user=os.getenv("POSTGRES_USER", "postgres"),
                    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                )
                logger.info("Postgres connection pool initialized")
            except OperationalError as e:
                logger.error("Failed to create Postgres pool: %s", e)
                cls._pool = None
                raise e
        return cls._pool

    @classmethod
    def check_health(cls) -> None:
        """
        Perform a simple health check by executing 'SELECT 1'.

        Raises:
            psycopg2.OperationalError: if Postgres is not reachable.
        """
        pool_instance = cls.get_pool()
        if pool_instance is None:
            raise OperationalError("Postgres pool not initialized")

        conn = pool_instance.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            logger.info("Postgres health check successful")
        finally:
            pool_instance.putconn(conn)
