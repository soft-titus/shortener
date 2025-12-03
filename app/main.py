"""
Main FastAPI application for the Shortener project.
"""

from fastapi import FastAPI

from app.helpers.logger import logger
from app.routes.health import router as health_router


app = FastAPI(title="URL Shortener API")

app.include_router(health_router)
logger.info("Health router registered at /health")

logger.info("FastAPI Shortener application initialized")
