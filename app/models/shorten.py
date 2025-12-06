"""
Pydantic models for shorten endpoints
"""

from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    """Incoming data for creating a short URL."""

    url: HttpUrl


class ShortenResponse(BaseModel):
    """Response with the generated short URL."""

    short_url: str
