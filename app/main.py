"""
Main FastAPI application for the URL Shortener project.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from redis import Redis, exceptions as redis_exceptions
from psycopg2 import pool, OperationalError

# Environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Redis config
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Postgres config
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "shortener")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Starting FastAPI app")

# Establish  Redis connection
redis_client = Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
)

# Establish Postgres connection
try:
    pg_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=20,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    logger.info("Postgres connection pool created successfully")  # pragma: no cover
except OperationalError as e:
    logger.error("Failed to create Postgres pool: %s", e)
    pg_pool = None

# FastAPI app
app = FastAPI()


@app.get("/health")
def health():
    """
    Health check endpoint that returns 200 if all dependencies is healthy.
    Returns 503 if any dependency is unavailable.
    """
    # Check Redis
    try:
        redis_client.ping()
        redis_status = "connected"
    except redis_exceptions.ConnectionError as e:
        redis_status = "not connected"
        logger.error("Redis not reachable: %s", e)
        raise HTTPException(status_code=503, detail=f"Redis is {redis_status}") from e

    # Check Postgres
    try:
        if pg_pool is None:
            raise OperationalError("Postgres pool not initialized")

        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            postgres_status = "connected"
        finally:
            pg_pool.putconn(conn)
    except OperationalError as e:
        postgres_status = "not connected"
        logger.error("Postgres not reachable: %s", e)
        raise HTTPException(
            status_code=503, detail=f"Postgres is {postgres_status}"
        ) from e

    return {"status": "ok", "redis": redis_status, "postgres": postgres_status}
