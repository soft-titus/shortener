"""
URL shortener service module.
"""

import logging

from psycopg2 import OperationalError, errors
from redis import exceptions as redis_exceptions

from app import config
from app.services.db import PostgresDB
from app.services.cache import RedisClient
from app.utils import generate_short_code

logger = logging.getLogger(__name__)


class OriginalURLAlreadyExists(Exception):
    """Raised when original_url already exists in DB."""


class ShortCodeGenerationFailed(Exception):
    """Raised when short code cannot be uniquely generated after retries."""


class ShortCodeNotFound(Exception):
    """Raised when short code does not exist in cache or database."""


class DatabaseUnavailable(Exception):
    """Raised when Postgres is unavailable."""


class ShortenerService:
    """Service layer for URL shortening and resolving."""

    @classmethod
    def shorten_url(cls, original_url: str) -> str:
        """
        Shorten a URL.

        Args:
            original_url (str): URL to shorten.

        Returns:
            str: Generated short code.

        Raises:
            OriginalURLAlreadyExists: if URL is already shortened
            ShortCodeGenerationFailed: if unique code cannot be generated
            DatabaseUnavailable: if DB is unreachable
        """
        code_len = config.SHORT_CODE_LENGTH
        max_retries = config.SHORT_CODE_MAX_RETRIES

        try:
            client = RedisClient.get_client()
            cached_code = client.get(f"url:{original_url}")
            if cached_code:
                logger.info(
                    "Cache hit for original URL: %s -> %s", original_url, cached_code
                )
                raise OriginalURLAlreadyExists(original_url)
        except redis_exceptions.RedisError:
            logger.debug("Redis unavailable during shorten, falling back to DB")

        try:
            exists = PostgresDB.original_url_exists(original_url)
        except OperationalError as exc:
            logger.error("Postgres unavailable when checking URL existence: %s", exc)
            raise DatabaseUnavailable("Database unavailable") from exc

        if exists:
            logger.info("Original URL already exists: %s", original_url)
            raise OriginalURLAlreadyExists(original_url)

        for attempt in range(1, max_retries + 1):
            short_code = generate_short_code(code_len)
            try:
                PostgresDB.insert_short_url(short_code, original_url)
                logger.info(
                    "Inserted mapping: %s -> %s (attempt %d)",
                    short_code,
                    original_url,
                    attempt,
                )
                break

            except errors.UniqueViolation:  # pylint: disable=no-member
                logger.warning(
                    "Collision for short code %s (attempt %d)", short_code, attempt
                )
                continue

            except OperationalError as exc:
                logger.error("Postgres operational error: %s", exc)
                raise DatabaseUnavailable("Database insert error") from exc
        else:
            raise ShortCodeGenerationFailed(
                f"Failed to generate unique short code after {max_retries} attempts"
            )

        try:
            RedisClient.set_with_ttl(f"short:{short_code}", original_url)
            RedisClient.set_with_ttl(f"url:{original_url}", short_code)
        except redis_exceptions.RedisError as exc:
            logger.warning("Failed to cache mapping in Redis: %s", exc)

        return short_code

    @staticmethod
    def resolve_short_code(short_code: str) -> str:
        """
        Resolve a short code to the original URL.

        Args:
            short_code (str): Short code to resolve.

        Returns:
            str: Original URL.

        Raises:
            ShortCodeNotFound: if code not found in cache or DB
            DatabaseUnavailable: if DB is unreachable
        """
        try:
            client = RedisClient.get_client()
            cached = client.get(f"short:{short_code}")
            if cached:
                logger.info("Cache hit for short code: %s", short_code)
                return cached
        except redis_exceptions.RedisError:
            logger.debug("Redis unavailable during resolve, falling back to DB")

        try:
            original = PostgresDB.get_original_url(short_code)
        except OperationalError as exc:
            logger.error("Postgres unavailable: %s", exc)
            raise DatabaseUnavailable("Database unavailable") from exc

        if original is None:
            logger.info("Short code not found: %s", short_code)
            raise ShortCodeNotFound(short_code)

        try:
            RedisClient.set_with_ttl(f"short:{short_code}", original)
            RedisClient.set_with_ttl(f"url:{original}", short_code)
        except redis_exceptions.RedisError:
            logger.debug("Failed to cache mapping after DB resolve")

        return original
