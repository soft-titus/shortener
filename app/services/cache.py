"""
Cache service module with Redis.
"""

import os
import logging
from redis import Redis, exceptions as redis_exceptions

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
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
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
