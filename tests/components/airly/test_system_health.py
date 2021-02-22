"""Test Airly system health."""
import asyncio
from unittest.mock import Mock

from aiohttp import ClientError

from openpeerpower.components.airly.const import DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import get_system_health_info


async def test_airly_system_health.opp, aioclient_mock):
    """Test Airly system health."""
    aioclient_mock.get("https://airapi.airly.eu/v2/", text="")
    opp.config.components.add(DOMAIN)
    assert await async_setup_component.opp, "system_health", {})

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN]["0123xyz"] = Mock(
        airly=Mock(AIRLY_API_URL="https://airapi.airly.eu/v2/")
    )

    info = await get_system_health_info.opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {"can_reach_server": "ok"}


async def test_airly_system_health_fail.opp, aioclient_mock):
    """Test Airly system health."""
    aioclient_mock.get("https://airapi.airly.eu/v2/", exc=ClientError)
    opp.config.components.add(DOMAIN)
    assert await async_setup_component.opp, "system_health", {})

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN]["0123xyz"] = Mock(
        airly=Mock(AIRLY_API_URL="https://airapi.airly.eu/v2/")
    )

    info = await get_system_health_info.opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {"can_reach_server": {"type": "failed", "error": "unreachable"}}
