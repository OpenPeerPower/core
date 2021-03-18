"""The tests for Open Peer Power frontend."""
from datetime import timedelta
import re
from unittest.mock import patch

import pytest

from openpeerpower.components.frontend import (
    CONF_EXTRA_HTML_URL,
    CONF_EXTRA_HTML_URL_ES5,
    CONF_JS_VERSION,
    CONF_THEMES,
    DOMAIN,
    EVENT_PANELS_UPDATED,
    THEMES_STORAGE_KEY,
)
from openpeerpower.components.websocket_api.const import TYPE_RESULT
from openpeerpower.const import HTTP_NOT_FOUND
from openpeerpower.loader import async_get_integration
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt

from tests.common import async_capture_events, async_fire_time_changed

CONFIG_THEMES = {
    DOMAIN: {
        CONF_THEMES: {
            "happy": {"primary-color": "red"},
            "dark": {"primary-color": "black"},
        }
    }
}


@pytest.fixture
async def ignore_frontend_deps(opp):
    """Frontend dependencies."""
    frontend = await async_get_integration(opp, "frontend")
    for dep in frontend.dependencies:
        if dep not in ("http", "websocket_api"):
            opp.config.components.add(dep)


@pytest.fixture
async def frontend(opp, ignore_frontend_deps):
    """Frontend setup with themes."""
    assert await async_setup_component(
        opp,
        "frontend",
        {},
    )


@pytest.fixture
async def frontend_themes(opp):
    """Frontend setup with themes."""
    assert await async_setup_component(
        opp,
        "frontend",
        CONFIG_THEMES,
    )


@pytest.fixture
async def mock_http_client(opp, aiohttp_client, frontend):
    """Start the Open Peer Power HTTP component."""
    return await aiohttp_client(opp.http.app)


@pytest.fixture
async def themes_ws_client(opp, opp_ws_client, frontend_themes):
    """Start the Open Peer Power HTTP component."""
    return await opp_ws_client(opp)


@pytest.fixture
async def ws_client(opp, opp_ws_client, frontend):
    """Start the Open Peer Power HTTP component."""
    return await opp_ws_client(opp)


@pytest.fixture
async def mock_http_client_with_urls(opp, aiohttp_client, ignore_frontend_deps):
    """Start the Open Peer Power HTTP component."""
    assert await async_setup_component(
        opp,
        "frontend",
        {
            DOMAIN: {
                CONF_JS_VERSION: "auto",
                CONF_EXTRA_HTML_URL: ["https://domain.com/my_extra_url.html"],
                CONF_EXTRA_HTML_URL_ES5: ["https://domain.com/my_extra_url_es5.html"],
            }
        },
    )
    return await aiohttp_client(opp.http.app)


@pytest.fixture
def mock_onboarded():
    """Mock that we're onboarded."""
    with patch(
        "openpeerpower.components.onboarding.async_is_onboarded", return_value=True
    ):
        yield


async def test_dont_cache_service_worker(mock_http_client):
    """Test that we don't cache the service worker."""
    resp = await mock_http_client.get("/service_worker.js")
    assert resp.status == 200
    assert "cache-control" not in resp.headers


async def test_404(mock_http_client):
    """Test for HTTP 404 error."""
    resp = await mock_http_client.get("/not-existing")
    assert resp.status == HTTP_NOT_FOUND


async def test_we_cannot_POST_to_root(mock_http_client):
    """Test that POST is not allow to root."""
    resp = await mock_http_client.post("/")
    assert resp.status == 405


async def test_themes_api(opp, themes_ws_client):
    """Test that /api/themes returns correct data."""
    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"
    assert msg["result"]["default_dark_theme"] is None
    assert msg["result"]["themes"] == {
        "happy": {"primary-color": "red"},
        "dark": {"primary-color": "black"},
    }

    # safe mode
    opp.config.safe_mode = True
    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "safe_mode"
    assert msg["result"]["themes"] == {
        "safe_mode": {"primary-color": "#db4437", "accent-color": "#ffca28"}
    }


async def test_themes_persist(opp, opp_storage, opp_ws_client, ignore_frontend_deps):
    """Test that theme settings are restores after restart."""
    opp_storage[THEMES_STORAGE_KEY] = {
        "key": THEMES_STORAGE_KEY,
        "version": 1,
        "data": {
            "frontend_default_theme": "happy",
            "frontend_default_dark_theme": "dark",
        },
    }

    assert await async_setup_component(opp, "frontend", CONFIG_THEMES)
    themes_ws_client = await opp_ws_client(opp)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "happy"
    assert msg["result"]["default_dark_theme"] == "dark"


async def test_themes_save_storage(opp, opp_storage, frontend_themes):
    """Test that theme settings are restores after restart."""

    await opp.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await opp.services.async_call(
        DOMAIN, "set_theme", {"name": "dark", "mode": "dark"}, blocking=True
    )

    # To trigger the call_later
    async_fire_time_changed(opp, dt.utcnow() + timedelta(seconds=60))
    # To execute the save
    await opp.async_block_till_done()

    assert opp_storage[THEMES_STORAGE_KEY]["data"] == {
        "frontend_default_theme": "happy",
        "frontend_default_dark_theme": "dark",
    }


async def test_themes_set_theme(opp, themes_ws_client):
    """Test frontend.set_theme service."""
    await opp.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "happy"

    await opp.services.async_call(
        DOMAIN, "set_theme", {"name": "default"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"

    await opp.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await opp.services.async_call(DOMAIN, "set_theme", {"name": "none"}, blocking=True)

    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"


async def test_themes_set_theme_wrong_name(opp, themes_ws_client):
    """Test frontend.set_theme service called with wrong name."""

    await opp.services.async_call(DOMAIN, "set_theme", {"name": "wrong"}, blocking=True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"


async def test_themes_set_dark_theme(opp, themes_ws_client):
    """Test frontend.set_theme service called with dark mode."""

    await opp.services.async_call(
        DOMAIN, "set_theme", {"name": "dark", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_dark_theme"] == "dark"

    await opp.services.async_call(
        DOMAIN, "set_theme", {"name": "default", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_dark_theme"] == "default"

    await opp.services.async_call(
        DOMAIN, "set_theme", {"name": "none", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_dark_theme"] is None


async def test_themes_set_dark_theme_wrong_name(opp, frontend, themes_ws_client):
    """Test frontend.set_theme service called with mode dark and wrong name."""
    await opp.services.async_call(
        DOMAIN, "set_theme", {"name": "wrong", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_dark_theme"] is None


async def test_themes_reload_themes(opp, frontend, themes_ws_client):
    """Test frontend.reload_themes service."""

    with patch(
        "openpeerpower.components.frontend.async_opp_config_yaml",
        return_value={DOMAIN: {CONF_THEMES: {"sad": {"primary-color": "blue"}}}},
    ):
        await opp.services.async_call(
            DOMAIN, "set_theme", {"name": "happy"}, blocking=True
        )
        await opp.services.async_call(DOMAIN, "reload_themes", blocking=True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    assert msg["result"]["themes"] == {"sad": {"primary-color": "blue"}}
    assert msg["result"]["default_theme"] == "default"


async def test_missing_themes(opp, ws_client):
    """Test that themes API works when themes are not defined."""
    await ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await ws_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["default_theme"] == "default"
    assert msg["result"]["themes"] == {}


async def test_get_panels(opp, opp_ws_client, mock_http_client):
    """Test get_panels command."""
    events = async_capture_events(opp, EVENT_PANELS_UPDATED)

    resp = await mock_http_client.get("/map")
    assert resp.status == HTTP_NOT_FOUND

    opp.components.frontend.async_register_built_in_panel(
        "map", "Map", "mdi:tooltip-account", require_admin=True
    )

    resp = await mock_http_client.get("/map")
    assert resp.status == 200

    assert len(events) == 1

    client = await opp_ws_client(opp)
    await client.send_json({"id": 5, "type": "get_panels"})

    msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["map"]["component_name"] == "map"
    assert msg["result"]["map"]["url_path"] == "map"
    assert msg["result"]["map"]["icon"] == "mdi:tooltip-account"
    assert msg["result"]["map"]["title"] == "Map"
    assert msg["result"]["map"]["require_admin"] is True

    opp.components.frontend.async_remove_panel("map")

    resp = await mock_http_client.get("/map")
    assert resp.status == HTTP_NOT_FOUND

    assert len(events) == 2


async def test_get_panels_non_admin(opp, ws_client, opp_admin_user):
    """Test get_panels command."""
    opp_admin_user.groups = []

    opp.components.frontend.async_register_built_in_panel(
        "map", "Map", "mdi:tooltip-account", require_admin=True
    )
    opp.components.frontend.async_register_built_in_panel(
        "history", "History", "mdi:history"
    )

    await ws_client.send_json({"id": 5, "type": "get_panels"})

    msg = await ws_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert "history" in msg["result"]
    assert "map" not in msg["result"]


async def test_get_translations(opp, ws_client):
    """Test get_translations command."""
    with patch(
        "openpeerpower.components.frontend.async_get_translations",
        side_effect=lambda opp, lang, category, integration, config_flow: {
            "lang": lang
        },
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_translations",
                "language": "nl",
                "category": "lang",
            }
        )
        msg = await ws_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {"resources": {"lang": "nl"}}


async def test_auth_load(opp):
    """Test auth component loaded by default."""
    frontend = await async_get_integration(opp, "frontend")
    assert "auth" in frontend.dependencies


async def test_onboarding_load(opp):
    """Test onboarding component loaded by default."""
    frontend = await async_get_integration(opp, "frontend")
    assert "onboarding" in frontend.dependencies


async def test_auth_authorize(mock_http_client):
    """Test the authorize endpoint works."""
    resp = await mock_http_client.get(
        "/auth/authorize?response_type=code&client_id=https://localhost/&"
        "redirect_uri=https://localhost/&state=123%23456"
    )
    assert resp.status == 200
    # No caching of auth page.
    assert "cache-control" not in resp.headers

    text = await resp.text()

    # Test we can retrieve authorize.js
    authorizejs = re.search(
        r"(?P<app>\/frontend_latest\/authorize.[A-Za-z0-9]{8}.js)", text
    )

    assert authorizejs is not None, text
    resp = await mock_http_client.get(authorizejs.groups(0)[0])
    assert resp.status == 200
    assert "public" in resp.headers.get("cache-control")


async def test_static_paths(opp, mock_http_client):
    """Test static paths."""
    resp = await mock_http_client.get(
        "/.well-known/change-password", allow_redirects=False
    )
    assert resp.status == 302
    assert resp.headers["location"] == "/profile"
