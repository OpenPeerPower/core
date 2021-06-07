"""Test ISY994 system health."""
import asyncio
from unittest.mock import Mock

from aiohttp import ClientError

from openpeerpower.components.isy994.const import DOMAIN, ISY994_ISY, ISY_URL_POSTFIX
from openpeerpower.const import CONF_HOST
from openpeerpower.setup import async_setup_component

from .test_config_flow import MOCK_HOSTNAME, MOCK_UUID

from tests.common import MockConfigEntry, get_system_health_info

MOCK_ENTRY_ID = "cad4af20b811990e757588519917d6af"
MOCK_CONNECTED = "connected"
MOCK_HEARTBEAT = "2021-05-01T00:00:00.000000"


async def test_system_health(opp, aioclient_mock):
    """Test system health."""
    aioclient_mock.get(f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}", text="")

    opp.config.components.add(DOMAIN)
    assert await async_setup_component(opp, "system_health", {})

    MockConfigEntry(
        domain=DOMAIN,
        entry_id=MOCK_ENTRY_ID,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}"},
        unique_id=MOCK_UUID,
    ).add_to_opp(opp)

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN][MOCK_ENTRY_ID] = {}
    opp.data[DOMAIN][MOCK_ENTRY_ID][ISY994_ISY] = Mock(
        connected=True,
        websocket=Mock(
            last_heartbeat=MOCK_HEARTBEAT,
            status=MOCK_CONNECTED,
        ),
    )

    info = await get_system_health_info(opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info["host_reachable"] == "ok"
    assert info["device_connected"]
    assert info["last_heartbeat"] == MOCK_HEARTBEAT
    assert info["websocket_status"] == MOCK_CONNECTED


async def test_system_health_failed_connect(opp, aioclient_mock):
    """Test system health."""
    aioclient_mock.get(f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}", exc=ClientError)

    opp.config.components.add(DOMAIN)
    assert await async_setup_component(opp, "system_health", {})

    MockConfigEntry(
        domain=DOMAIN,
        entry_id=MOCK_ENTRY_ID,
        data={CONF_HOST: f"http://{MOCK_HOSTNAME}"},
        unique_id=MOCK_UUID,
    ).add_to_opp(opp)

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN][MOCK_ENTRY_ID] = {}
    opp.data[DOMAIN][MOCK_ENTRY_ID][ISY994_ISY] = Mock(
        connected=True,
        websocket=Mock(
            last_heartbeat=MOCK_HEARTBEAT,
            status=MOCK_CONNECTED,
        ),
    )

    info = await get_system_health_info(opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info["host_reachable"] == {"error": "unreachable", "type": "failed"}
