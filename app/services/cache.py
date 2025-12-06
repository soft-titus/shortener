"""
Cache service module with Redis.
"""

import logging
from redis import Redis, exceptions as redis_exceptions

from app import config

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Singleton wrapper for Redis client.
    """

    _instance: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        """
        Get the Redis client instance.
        Initializes the client if it hasn't been created yet.
        """
        if cls._instance is None:
            cls._instance = Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True,
            )
            logger.info("Redis client initialized")
        return cls._instance

    @classmethod
    def check_health(cls) -> None:
        """
        Perform a simple health check on Redis by pinging the server.

        Raises:
            redis.exceptions.ConnectionError: if Redis is not reachable.
        """
        client = cls.get_client()
        try:
            client.ping()
            logger.info("Redis ping successful")
        except redis_exceptions.ConnectionError as e:
            logger.error("Redis ping failed: %s", e)
            raise e

    @classmethod
    def set_with_ttl(cls, key: str, value: str, ttl: int | None = None) -> None:
        """
        Set a key-value pair in Redis with a TTL.

        Args:
            key (str): Redis key.
            value (str): Value to store.
            ttl (int | None): Time-to-live in seconds.
        """
        client = cls.get_client()

        if ttl is None:
            ttl_hours = config.CACHE_TTL_HOURS
            ttl = ttl_hours * 60 * 60

        try:
            client.setex(name=key, time=ttl, value=value)
            logger.info("Set key in Redis with TTL=%s seconds: %s", ttl, key)
        except redis_exceptions.RedisError as e:
            logger.warning("Failed to set key in Redis: %s", e)

    @classmethod
    def get_all_visit_keys(cls) -> list[str]:
        """
        Get all Redis keys for visit counters.

        Returns:
            list[str]: List of keys, empty list if none or on Redis failure.
        """
        client = cls.get_client()
        keys = []

        try:
            cursor = 0
            while True:
                cursor, batch = client.scan(cursor=cursor, match="visits:*", count=100)
                keys.extend(batch)
                if cursor == 0:
                    break
            return keys
        except redis_exceptions.RedisError as e:
            logger.warning("Failed to fetch visit keys from Redis: %s", e)
            return []

    @classmethod
    def get_visit_count(cls, short_code: str) -> int | None:
        """
        Get the visit count for short code.

        Args:
            short_code (str): short code to fetch the visits count

        Returns:
            int | None: Current visit count, 0 if short code doesn't exist, or None if Redis fails.
        """
        client = cls.get_client()

        try:
            value = client.get(f"visits:{short_code}")
            if value is None:
                return 0
            return int(value)
        except (redis_exceptions.RedisError, ValueError) as e:
            logger.warning("Failed to get visit count for %s: %s", short_code, e)
            return None

    @classmethod
    def increment_visit_count(cls, short_code: str, amount: int = 1) -> int | None:
        """
        Increment a visit counter for short code by a specified amount.

        Args:
            short_code (str): short code for visit count
            amount (int): How much to increment by (default: 1)

        Returns:
            int | None: The new counter value, or None if Redis fails.
        """
        client = cls.get_client()

        try:
            new_count = client.incrby(f"visits:{short_code}", amount)
            logger.info(
                "Incremented visit count for %s by %s -> %s",
                short_code,
                amount,
                new_count,
            )
            return new_count
        except redis_exceptions.RedisError as e:
            logger.warning("Failed to increment visit count for %s: %s", short_code, e)
            return None

    @classmethod
    def decrement_visit_count(cls, short_code: str, amount: int = 1) -> int | None:
        """
        Decrement a visit counter for short code by a specified amount.

        Args:
            short_code (str): short code for visit count
            amount (int): How much to decrement by (default: 1)

        Returns:
            int | None: The new counter value, or None if Redis fails.
        """
        client = cls.get_client()

        try:
            new_count = client.decrby(f"visits:{short_code}", amount)
            logger.info(
                "Decremented visit count for %s by %s -> %s",
                short_code,
                amount,
                new_count,
            )

            if new_count <= 0:
                client.delete(f"visits:{short_code}")
                logger.info(
                    "Deleted visit counter for %s because count reached zero",
                    short_code,
                )

            return new_count
        except redis_exceptions.RedisError as e:
            logger.warning("Failed to decrement visit count for %s: %s", short_code, e)
            return None
