"""
Health router
"""

from fastapi import APIRouter, HTTPException
from app.helpers.logger import logger
from app.services.db import PostgresDB
from app.services.cache import RedisClient

router = APIRouter()


@router.get(
    "/health",
    summary="Health check for all dependencies",
    responses={
        200: {
            "description": "All dependencies are healthy.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "redis": "connected",
                        "postgres": "connected",
                    }
                }
            },
        },
        503: {
            "description": "One or more dependencies are unreachable.",
            "content": {
                "application/json": {
                    "examples": {
                        "redis_down": {
                            "summary": "Redis unreachable",
                            "value": {"detail": "Redis: not connected"},
                        },
                        "postgres_down": {
                            "summary": "Postgres unreachable",
                            "value": {"detail": "Postgres: not connected"},
                        },
                    }
                }
            },
        },
    },
)
def health():
    """
    Health check endpoint ensuring dependencies are reachable.
    Returns 200 if healthy, 503 if any dependency fails.
    """
    logger.info("Health endpoint hit")

    try:
        RedisClient.check_health()
        redis_status = "connected"
        logger.info("Redis connection OK")
    except Exception as e:
        logger.error("Redis connection FAILED: %s", e)
        raise HTTPException(status_code=503, detail="Redis: not connected") from e

    try:
        PostgresDB.check_health()
        postgres_status = "connected"
        logger.info("Postgres connection OK")
    except Exception as e:
        logger.error("Postgres connection FAILED: %s", e)
        raise HTTPException(status_code=503, detail="Postgres: not connected") from e

    logger.info("Health endpoint : success")

    return {
        "status": "ok",
        "redis": redis_status,
        "postgres": postgres_status,
    }
