"""
Flush Redis visit counters into Postgres in bulk.
"""

from __future__ import annotations

import logging

from psycopg2 import OperationalError


from app.config import LOG_LEVEL
from app.services.cache import RedisClient
from app.services.db import PostgresDB


logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def extract_short_code(redis_key: str) -> str | None:
    """
    Extract short code from a Redis key like: visits:<short_code>.

    Args:
        redis_key (str): Redis key

    Returns:
        str | None: Short code if valid, else None.
    """
    if not redis_key.startswith("visits:"):
        return None

    short_code = redis_key.removeprefix("visits:")
    return short_code or None


def main() -> None:
    """Main execution entrypoint."""
    logger.info("Starting visit counter flush job")

    keys = RedisClient.get_all_visit_keys()
    if not keys:
        logger.info("No visit keys found in Redis; nothing to flush")
        return

    visit_data: dict[str, int] = {}

    for redis_key in keys:
        short_code = extract_short_code(redis_key)
        if short_code is None:
            logger.warning("Ignoring invalid visit key: %s", redis_key)
            continue

        count = RedisClient.get_visit_count(short_code)
        if count is None:
            logger.warning("Skipping %s due to Redis fetch failure", short_code)
            continue

        if count > 0:
            visit_data[short_code] = count

    if not visit_data:
        logger.info("No valid visit counters to flush")
        return

    logger.info("Flushing %d visit counters to Postgres...", len(visit_data))

    try:
        PostgresDB.increment_visits_bulk(visit_data)
    except OperationalError as e:
        logger.error("Failed to update Postgres: %s", e)
        logger.error("Abort flush, Redis counters left untouched")
        return

    for short_code, count in visit_data.items():
        new_val = RedisClient.decrement_visit_count(short_code, count)
        if new_val is None:
            logger.warning("Failed to decrement Redis counter for %s", short_code)

    logger.info("Flush complete, %d counters applied", len(visit_data))


if __name__ == "__main__":
    main()  # pragma: no cover
