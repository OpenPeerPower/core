"""Fixtures for websocket tests."""
import pytest

from openpeerpower.components.websocket_api.auth import TYPE_AUTH_REQUIRED
from openpeerpower.components.websocket_api.http import URL
from openpeerpowerr.setup import async_setup_component


@pytest.fixture
async def websocket_client.opp,.opp_ws_client):
    """Create a websocket client."""
    return await opp._ws_client.opp)


@pytest.fixture
async def no_auth_websocket_client.opp, aiohttp_client):
    """Websocket connection that requires authentication."""
    assert await async_setup_component.opp, "websocket_api", {})
    await opp..async_block_till_done()

    client = await aiohttp_client.opp.http.app)
    ws = await client.ws_connect(URL)

    auth_ok = await ws.receive_json()
    assert auth_ok["type"] == TYPE_AUTH_REQUIRED

    ws.client = client
    yield ws

    if not ws.closed:
        await ws.close()
