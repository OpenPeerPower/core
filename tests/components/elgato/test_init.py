"""Tests for the Elgato Key Light integration."""
import aiohttp

from openpeerpower.components.elgato.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_RETRY
from openpeerpower.core import OpenPeerPower

from tests.components.elgato import init_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Elgato Key Light configuration entry not ready."""
    aioclient_mock.get(
        "http://127.0.0.1:9123/elgato/accessory-info", exc=aiohttp.ClientError
    )

    entry = await init_integration(opp, aioclient_mock)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Elgato Key Light configuration entry unloading."""
    entry = await init_integration(opp, aioclient_mock)
    assert opp.data[DOMAIN]

    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
    assert not opp.data.get(DOMAIN)
