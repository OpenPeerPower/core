"""Test cases for the API stream sensor."""

from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components.websocket_api.auth import TYPE_AUTH_REQUIRED
from openpeerpower.components.websocket_api.http import URL

from .test_auth import test_auth_active_with_token


async def test_websocket_api(opp, aiohttp_client, opp_access_token, legacy_auth):
    """Test API streams."""
    await async_setup_component(
        opp. "sensor", {"sensor": {"platform": "websocket_api"}}
    )
    await opp.async_block_till_done()

    client = await aiohttp_client.opp.http.app)
    ws = await client.ws_connect(URL)

    auth_ok = await ws.receive_json()

    assert auth_ok["type"] == TYPE_AUTH_REQUIRED

    ws.client = client

    state = opp.states.get("sensor.connected_clients")
    assert state.state == "0"

    await test_auth_active_with_token(opp, ws, opp_access_token)

    state = opp.states.get("sensor.connected_clients")
    assert state.state == "1"

    await ws.close()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.connected_clients")
    assert state.state == "0"
