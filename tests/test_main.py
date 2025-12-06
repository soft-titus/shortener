"""Tests for the FastAPI main application entrypoint."""

from app.main import app


def test_health_route_registered():
    """Ensure /health endpoint is registered."""
    routes = {route.path: route.methods for route in app.router.routes}
    assert "/health" in routes
    assert "GET" in routes["/health"]


def test_shorten_route_registered():
    """Ensure /s endpoints are registered."""
    routes = {route.path: route.methods for route in app.router.routes}
    assert "/s/" in routes
    assert "POST" in routes["/s/"]
    assert "/s/{short_code}" in routes
    assert "GET" in routes["/s/{short_code}"]


def test_stat_route_registered():
    """Ensure /stat endpoints are registered."""
    routes = {route.path: route.methods for route in app.router.routes}
    assert "/stat/{short_code}" in routes
    assert "GET" in routes["/stat/{short_code}"]
