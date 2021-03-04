"""Test cors for the HTTP component."""
from pathlib import Path
from unittest.mock import patch

from aiohttp import web
from aiohttp.hdrs import (
    ACCESS_CONTROL_ALLOW_HEADERS,
    ACCESS_CONTROL_ALLOW_ORIGIN,
    ACCESS_CONTROL_REQUEST_HEADERS,
    ACCESS_CONTROL_REQUEST_METHOD,
    AUTHORIZATION,
    ORIGIN,
)
import pytest

from openpeerpower.components.http.cors import setup_cors
from openpeerpower.components.http.view import OpenPeerPowerView
from openpeerpower.setup import async_setup_component

from . import HTTP_HEADER_HA_AUTH

TRUSTED_ORIGIN = "https://openpeerpower.io"


async def test_cors_middleware_loaded_by_default(opp):
    """Test accessing to server from banned IP when feature is off."""
    with patch("openpeerpower.components.http.setup_cors") as mock_setup:
        await async_setup_component(opp, "http", {"http": {}})

    assert len(mock_setup.mock_calls) == 1


async def test_cors_middleware_loaded_from_config(opp):
    """Test accessing to server from banned IP when feature is off."""
    with patch("openpeerpower.components.http.setup_cors") as mock_setup:
        await async_setup_component(
            opp,
            "http",
            {"http": {"cors_allowed_origins": ["http://openpeerpower.io"]}},
        )

    assert len(mock_setup.mock_calls) == 1


async def mock_handler(request):
    """Return if request was authenticated."""
    return web.Response(status=200)


@pytest.fixture
def client(loop, aiohttp_client):
    """Fixture to set up a web.Application."""
    app = web.Application()
    app.router.add_get("/", mock_handler)
    setup_cors(app, [TRUSTED_ORIGIN])
    return loop.run_until_complete(aiohttp_client(app))


async def test_cors_requests(client):
    """Test cross origin requests."""
    req = await client.get("/", headers={ORIGIN: TRUSTED_ORIGIN})
    assert req.status == 200
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN

    # With password in URL
    req = await client.get(
        "/", params={"api_password": "some-pass"}, headers={ORIGIN: TRUSTED_ORIGIN}
    )
    assert req.status == 200
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN

    # With password in headers
    req = await client.get(
        "/", headers={HTTP_HEADER_HA_AUTH: "some-pass", ORIGIN: TRUSTED_ORIGIN}
    )
    assert req.status == 200
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN

    # With auth token in headers
    req = await client.get(
        "/", headers={AUTHORIZATION: "Bearer some-token", ORIGIN: TRUSTED_ORIGIN}
    )
    assert req.status == 200
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN


async def test_cors_preflight_allowed(client):
    """Test cross origin resource sharing preflight (OPTIONS) request."""
    req = await client.options(
        "/",
        headers={
            ORIGIN: TRUSTED_ORIGIN,
            ACCESS_CONTROL_REQUEST_METHOD: "GET",
            ACCESS_CONTROL_REQUEST_HEADERS: "x-requested-with",
        },
    )

    assert req.status == 200
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN
    assert req.headers[ACCESS_CONTROL_ALLOW_HEADERS] == "X-REQUESTED-WITH"


async def test_cors_middleware_with_cors_allowed_view(opp):
    """Test that we can configure cors and have a cors_allowed view."""

    class MyView(OpenPeerPowerView):
        """Test view that allows CORS."""

        requires_auth = False
        cors_allowed = True

        def __init__(self, url, name):
            """Initialize test view."""
            self.url = url
            self.name = name

        async def get(self, request):
            """Test response."""
            return "test"

    assert await async_setup_component(
        opp, "http", {"http": {"cors_allowed_origins": ["http://openpeerpower.io"]}}
    )

    opp.http.register_view(MyView("/api/test", "api:test"))
    opp.http.register_view(MyView("/api/test", "api:test2"))
    opp.http.register_view(MyView("/api/test2", "api:test"))

    opp.http.app._on_startup.freeze()
    await opp.http.app.startup()


async def test_cors_works_with_frontend(opp, opp_client):
    """Test CORS works with the frontend."""
    assert await async_setup_component(
        opp,
        "frontend",
        {"http": {"cors_allowed_origins": ["http://openpeerpower.io"]}},
    )
    client = await opp_client()
    resp = await client.get("/")
    assert resp.status == 200


async def test_cors_on_static_files(opp, opp_client):
    """Test that we enable CORS for static files."""
    assert await async_setup_component(
        opp, "frontend", {"http": {"cors_allowed_origins": ["http://www.example.com"]}}
    )
    opp.http.register_static_path("/something", str(Path(__file__).parent))

    client = await opp_client()
    resp = await client.options(
        "/something/__init__.py",
        headers={
            "origin": "http://www.example.com",
            ACCESS_CONTROL_REQUEST_METHOD: "GET",
        },
    )
    assert resp.status == 200
    assert resp.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == "http://www.example.com"
