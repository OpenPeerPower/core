"""Test GIOS system health."""
import asyncio

from aiohttp import ClientError

from openpeerpower.components.gios.const import DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import get_system_health_info


async def test_gios_system_health.opp, aioclient_mock):
    """Test GIOS system health."""
    aioclient_mock.get("http://api.gios.gov.pl/", text="")
    opp.config.components.add(DOMAIN)
    assert await async_setup_component.opp, "system_health", {})

    info = await get_system_health_info.opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {"can_reach_server": "ok"}


async def test_gios_system_health_fail.opp, aioclient_mock):
    """Test GIOS system health."""
    aioclient_mock.get("http://api.gios.gov.pl/", exc=ClientError)
    opp.config.components.add(DOMAIN)
    assert await async_setup_component.opp, "system_health", {})

    info = await get_system_health_info.opp, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    assert info == {"can_reach_server": {"type": "failed", "error": "unreachable"}}
