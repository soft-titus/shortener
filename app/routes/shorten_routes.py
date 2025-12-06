"""
FastAPI routes for URL shortening
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.models.shorten import ShortenRequest, ShortenResponse
from app.services.shortener import (
    ShortenerService,
    OriginalURLAlreadyExists,
    ShortCodeGenerationFailed,
    ShortCodeNotFound,
    DatabaseUnavailable,
)
from app import config

router = APIRouter(
    prefix="/s",
    tags=["shorten"],
)


@router.post(
    "/",
    response_model=ShortenResponse,
    summary="Create a short URL",
    responses={
        200: {
            "description": "Short URL created successfully",
            "content": {
                "application/json": {
                    "example": {"short_url": "https://example.com/s/abc123"}
                }
            },
        },
        409: {
            "description": "URL has already been shortened",
            "content": {
                "application/json": {
                    "example": {"detail": "This URL has already been shortened."}
                }
            },
        },
        500: {
            "description": "Short code generation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to generate unique short code"}
                }
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
def create_short_url(payload: ShortenRequest):
    """
    Generate a new short URL for a provided `url`.
    """
    try:
        short_code = ShortenerService.shorten_url(str(payload.url))

    except OriginalURLAlreadyExists:
        raise HTTPException(
            status_code=409,
            detail="This URL has already been shortened.",
        ) from None

    except ShortCodeGenerationFailed as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except DatabaseUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        ) from None

    short_url = f"{config.BASE_URL}/s/{short_code}"
    return ShortenResponse(short_url=short_url)


@router.get(
    "/{short_code}",
    summary="Redirect using a short code",
    responses={
        307: {
            "description": "Temporary redirect to the original URL",
            "headers": {
                "Location": {
                    "description": "Target URL",
                    "schema": {"type": "string", "format": "uri"},
                }
            },
        },
        404: {
            "description": "Short code not found",
            "content": {
                "application/json": {"example": {"detail": "Short code not found."}}
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
def redirect_short_url(short_code: str):
    """
    Resolve a short code and redirect to the original URL.
    """
    try:
        original_url = ShortenerService.resolve_short_code(short_code)

    except ShortCodeNotFound:
        raise HTTPException(
            status_code=404,
            detail="Short code not found.",
        ) from None

    except DatabaseUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        ) from None

    return RedirectResponse(url=original_url, status_code=307)
