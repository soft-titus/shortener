"""
FastAPI routes for statistics retrieval.
"""

from fastapi import APIRouter, HTTPException
from psycopg2 import OperationalError

from app.models.statistic import StatResponse
from app.services.db import PostgresDB

router = APIRouter(
    prefix="/stat",
    tags=["stat"],
)


@router.get(
    "/{short_code}",
    response_model=StatResponse,
    summary="Retrieve statistics for a short code",
    responses={
        200: {
            "description": "Statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "short_code": "abc123",
                        "original_url": "https://example.com",
                        "visits": 42,
                        "created": "2025-01-01T12:34:56",
                    }
                }
            },
        },
        404: {
            "description": "Short code not found",
            "content": {
                "application/json": {"example": {"detail": "Short code not found"}}
            },
        },
        503: {
            "description": "Database unavailable",
            "content": {
                "application/json": {"example": {"detail": "Database is unavailable."}}
            },
        },
    },
)
def get_short_url_stats(short_code: str) -> StatResponse:
    """Retrieve statistics for a given short code."""

    try:
        result = PostgresDB.get_short_url_stat(short_code)
    except OperationalError:
        raise HTTPException(
            status_code=503, detail="Database is unavailable."
        ) from None

    if not result:
        raise HTTPException(status_code=404, detail="Short code not found")

    return StatResponse(
        short_code=result["short_code"],
        original_url=result["original_url"],
        visits=result["visits"],
        created=result["created_at"],
    )
