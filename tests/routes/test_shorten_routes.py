"""
Tests for the /s endpoint.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app import config
from app.services.shortener import (
    OriginalURLAlreadyExists,
    ShortCodeGenerationFailed,
    ShortCodeNotFound,
    DatabaseUnavailable,
)

client = TestClient(app)


def test_create_short_url_success():
    """POST /s/ returns 200 and full short URL."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.shorten_url",
        return_value="abc123",
    ):
        response = client.post("/s/", json={"url": "https://google.com"})

    assert response.status_code == 200
    assert response.json() == {"short_url": f"{config.BASE_URL}/s/abc123"}


def test_create_short_url_conflict():
    """POST /s/ returns 409 when URL already shortened."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.shorten_url",
        side_effect=OriginalURLAlreadyExists("https://google.com"),
    ):
        response = client.post("/s/", json={"url": "https://google.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "This URL has already been shortened."}


def test_create_short_url_generation_failed():
    """POST /s/ returns 500 when short code cannot be generated."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.shorten_url",
        side_effect=ShortCodeGenerationFailed("Failed to generate unique short code"),
    ):
        response = client.post("/s/", json={"url": "https://google.com"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to generate unique short code"}


def test_create_short_url_db_unavailable():
    """POST /s/ returns 503 when DB is unavailable."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.shorten_url",
        side_effect=DatabaseUnavailable("Database unavailable"),
    ):
        response = client.post("/s/", json={"url": "https://google.com"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_redirect_short_url_success():
    """GET /s/{code} returns 307 redirect."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.resolve_short_code",
        return_value="https://google.com",
    ):
        response = client.get("/s/abc123", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://google.com"


def test_redirect_short_url_not_found():
    """GET /s/{code} returns 404 for missing code."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.resolve_short_code",
        side_effect=ShortCodeNotFound("abc123"),
    ):
        response = client.get("/s/abc123")

    assert response.status_code == 404
    assert response.json() == {"detail": "Short code not found."}


def test_redirect_short_url_db_unavailable():
    """GET /s/{code} returns 503 when DB unavailable."""
    with patch(
        "app.routes.shorten_routes.ShortenerService.resolve_short_code",
        side_effect=DatabaseUnavailable("Database unavailable"),
    ):
        response = client.get("/s/abc123")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}
