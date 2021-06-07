"""The tests for the analytics ."""
from unittest.mock import patch

from openpeerpower.components.analytics.const import ANALYTICS_ENDPOINT_URL, DOMAIN
from openpeerpower.setup import async_setup_component

MOCK_VERSION = "1970.1.0"


async def test_setup(opp):
    """Test setup of the integration."""
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {}})
    await opp.async_block_till_done()

    assert DOMAIN in opp.data


async def test_websocket(opp, opp_ws_client, aioclient_mock):
    """Test websocekt commands."""
    aioclient_mock.post(ANALYTICS_ENDPOINT_URL, status=200)
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {}})
    await opp.async_block_till_done()

    ws_client = await opp_ws_client(opp)
    await ws_client.send_json({"id": 1, "type": "analytics"})

    response = await ws_client.receive_json()

    assert response["success"]

    with patch("openpeerpower.components.analytics.analytics.HA_VERSION", MOCK_VERSION):
        await ws_client.send_json(
            {"id": 2, "type": "analytics/preferences", "preferences": {"base": True}}
        )
        response = await ws_client.receive_json()
    assert len(aioclient_mock.mock_calls) == 1
    assert response["result"]["preferences"]["base"]

    await ws_client.send_json({"id": 3, "type": "analytics"})
    response = await ws_client.receive_json()
    assert response["result"]["preferences"]["base"]
