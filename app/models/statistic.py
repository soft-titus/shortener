"""
Pydantic models for stat endpoints
"""

from datetime import datetime
from pydantic import BaseModel, HttpUrl


class StatResponse(BaseModel):
    """Response model for a short code's statistic."""

    short_code: str
    original_url: HttpUrl
    visits: int
    created: datetime
