"""
Main FastAPI application for the Shortener project.
"""

from fastapi import FastAPI

from app.helpers.logger import logger
from app.routes.health_routes import router as health_router
from app.routes.shorten_routes import router as shorten_router
from app.routes.stat_routes import router as stat_router


app = FastAPI(title="URL Shortener API")

app.include_router(health_router)
logger.info("Health router registered at /health")

app.include_router(shorten_router)
logger.info("Shorten router registered at /s")

app.include_router(stat_router)
logger.info("Stat router registered at /stat")

logger.info("FastAPI Shortener application initialized")
