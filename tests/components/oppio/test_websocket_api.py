"""Test websocket API."""
from openpeerpower.components.oppio.const import (
    ATTR_DATA,
    ATTR_ENDPOINT,
    ATTR_METHOD,
    ATTR_WS_EVENT,
    EVENT_SUPERVISOR_EVENT,
    WS_ID,
    WS_TYPE,
    WS_TYPE_API,
    WS_TYPE_SUBSCRIBE,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.setup import async_setup_component

from . import mock_all  # noqa: F401

from tests.common import async_mock_signal


async def test_ws_subscription(oppio_env, opp: OpenPeerPower, opp_ws_client):
    """Test websocket subscription."""
    assert await async_setup_component(opp, "oppio", {})
    client = await opp_ws_client(opp)
    await client.send_json({WS_ID: 5, WS_TYPE: WS_TYPE_SUBSCRIBE})
    response = await client.receive_json()
    assert response["success"]

    calls = async_mock_signal(opp, EVENT_SUPERVISOR_EVENT)
    async_dispatcher_send(opp, EVENT_SUPERVISOR_EVENT, {"lorem": "ipsum"})

    response = await client.receive_json()
    assert response["event"]["lorem"] == "ipsum"
    assert len(calls) == 1

    await client.send_json(
        {
            WS_ID: 6,
            WS_TYPE: "supervisor/event",
            ATTR_DATA: {ATTR_WS_EVENT: "test", "lorem": "ipsum"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert len(calls) == 2

    response = await client.receive_json()
    assert response["event"]["lorem"] == "ipsum"

    # Unsubscribe
    await client.send_json({WS_ID: 7, WS_TYPE: "unsubscribe_events", "subscription": 5})
    response = await client.receive_json()
    assert response["success"]


async def test_websocket_supervisor_api(
    oppio_env, opp: OpenPeerPower, opp_ws_client, aioclient_mock
):
    """Test Supervisor websocket api."""
    assert await async_setup_component(opp, "oppio", {})
    websocket_client = await opp_ws_client(opp)
    aioclient_mock.post(
        "http://127.0.0.1/snapshots/new/partial",
        json={"result": "ok", "data": {"slug": "sn_slug"}},
    )

    await websocket_client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/snapshots/new/partial",
            ATTR_METHOD: "post",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["result"]["slug"] == "sn_slug"

    await websocket_client.send_json(
        {
            WS_ID: 2,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/supervisor/info",
            ATTR_METHOD: "get",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["result"]["version_latest"] == "1.0.0"
