"""
Database service module with Postgres.
"""

import logging
from typing import Optional
from psycopg2 import pool, OperationalError, errors
from psycopg2.extras import RealDictCursor
from app import config

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
                    host=config.POSTGRES_HOST,
                    port=config.POSTGRES_PORT,
                    dbname=config.POSTGRES_DB,
                    user=config.POSTGRES_USER,
                    password=config.POSTGRES_PASSWORD,
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

    @classmethod
    def original_url_exists(cls, original_url: str) -> bool | None:
        """
        Check if the original URL already exists in database.

        Args:
            original_url (str): The original URL to look up.

        Returns:
            bool : True if exists, else False.
        """
        pool_instance = cls.get_pool()
        conn = pool_instance.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT original_url FROM short_urls WHERE original_url = %s",
                    (original_url,),
                )
                row = cur.fetchone()
                return bool(row)
        finally:
            pool_instance.putconn(conn)

    @classmethod
    def insert_short_url(cls, short_code: str, original_url: str) -> str:
        """
        Insert a new short URL into the database.

        Args:
            short_code (str): The generated short code.
            original_url (str): The original URL to store.

        Returns:
            short_code (str): The inserted short code.

        Raises:
            psycopg2.OperationalError if DB insertion fails.
        """
        pool_instance = cls.get_pool()
        conn = pool_instance.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO short_urls (short_code, original_url)
                    VALUES (%s, %s)
                    RETURNING short_code
                    """,
                    (short_code, original_url),
                )
                conn.commit()
                logger.info("Inserted short URL: %s -> %s", short_code, original_url)
                return short_code
        except errors.UniqueViolation:  # pylint: disable=no-member
            conn.rollback()
            raise
        except OperationalError as e:
            conn.rollback()
            logger.error("DB error while inserting short URL: %s", e)
            raise e
        finally:
            pool_instance.putconn(conn)

    @classmethod
    def get_original_url(cls, short_code: str) -> str | None:
        """
        Retrieve the original URL for a given short code.

        Args:
            short_code (str): The short code to look up.

        Returns:
            str | None: Original URL if found, else None.
        """
        pool_instance = cls.get_pool()
        conn = pool_instance.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT original_url FROM short_urls WHERE short_code = %s",
                    (short_code,),
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            pool_instance.putconn(conn)

    @classmethod
    def increment_visits_bulk(cls, visit_data: dict[str, int]) -> None:
        """
        Bulk increment 'visits' for multiple short codes in a single query.

        Args:
            visit_data (dict[str, int]): Mapping of short_code -> visit_count.

        Raises:
            OperationalError: If DB operation fails.
        """
        if not visit_data:
            return

        pool_instance = cls.get_pool()
        conn = pool_instance.getconn()
        try:
            with conn.cursor() as cur:
                values_str = ",".join(
                    cur.mogrify("(%s, %s)", (short_code, count)).decode("utf-8")
                    for short_code, count in visit_data.items()
                )
                sql = f"""
                    UPDATE short_urls AS s
                    SET visits = s.visits + v.count
                    FROM (VALUES {values_str}) AS v(short_code, count)
                    WHERE s.short_code = v.short_code
                """
                cur.execute(sql)

            conn.commit()
            logger.info("Bulk incremented visits for %d short codes", len(visit_data))
        except OperationalError as e:
            conn.rollback()
            logger.error("Failed to bulk increment visits: %s", e)
            raise e
        finally:
            pool_instance.putconn(conn)

    @classmethod
    def get_short_url_stat(cls, short_code: str) -> Optional[dict]:
        """
        Fetch statistics for a given short code.

        Args:
            short_code (str): Short code to query.

        Returns:
            Optional[dict]: Dictionary with keys 'short_code', 'original_url',
            'visits', 'created_at', or None if not found.
        """
        pool_instance = cls.get_pool()
        conn = pool_instance.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT short_code, original_url, visits, created_at
                    FROM short_urls
                    WHERE short_code = %s
                    """,
                    (short_code,),
                )
                result = cur.fetchone()
        finally:
            pool_instance.putconn(conn)

        return result
