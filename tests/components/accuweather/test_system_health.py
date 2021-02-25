"""Test AccuWeather system health."""
import asyncio
from unittest.mock import Mock

from aiohttp import ClientError

from openpeerpower.components.accuweather.const import COORDINATOR, DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import get_system_health_info


async def test_accuweather_system_health(opp, aioclient_mock):
    """Test AccuWeather system health."""
    aioclient_mock.get("https://dataservice.accuweather.com/", text="")
    opp.config.components.add(DOMAIN)
    assert await async_setup_component(opp, "system_health", {})

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN]["0123xyz"] = {}
    opp.data[DOMAIN]["0123xyz"][COORDINATOR] = Mock(
        accuweather=Mock(requests_remaining="42")
    )

    info = await get_system_health_info(opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {
        "can_reach_server": "ok",
        "remaining_requests": "42",
    }


async def test_accuweather_system_health_fail(opp, aioclient_mock):
    """Test AccuWeather system health."""
    aioclient_mock.get("https://dataservice.accuweather.com/", exc=ClientError)
    opp.config.components.add(DOMAIN)
    assert await async_setup_component(opp, "system_health", {})

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN]["0123xyz"] = {}
    opp.data[DOMAIN]["0123xyz"][COORDINATOR] = Mock(
        accuweather=Mock(requests_remaining="0")
    )

    info = await get_system_health_info(opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {
        "can_reach_server": {"type": "failed", "error": "unreachable"},
        "remaining_requests": "0",
    }
