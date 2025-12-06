"""
Configuration, read from environment variable
"""

import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_READONLY_HOST = os.getenv("POSTGRES_READONLY_HOST", POSTGRES_HOST)
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "shortener")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "168"))
SHORT_CODE_LENGTH = int(os.getenv("SHORT_CODE_LENGTH", "8"))
SHORT_CODE_MAX_RETRIES = int(os.getenv("SHORT_CODE_MAX_RETRIES", "10"))
