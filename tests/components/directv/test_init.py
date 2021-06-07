"""Tests for the DirecTV integration."""
from openpeerpower.components.directv.const import DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.core import OpenPeerPower

from tests.components.directv import setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker

# pylint: disable=redefined-outer-name


async def test_config_entry_not_ready(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the DirecTV configuration entry not ready."""
    entry = await setup_integration(opp, aioclient_mock, setup_error=True)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the DirecTV configuration entry unloading."""
    entry = await setup_integration(opp, aioclient_mock)

    assert entry.entry_id in opp.data[DOMAIN]
    assert entry.state is ConfigEntryState.LOADED

    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.entry_id not in opp.data[DOMAIN]
    assert entry.state is ConfigEntryState.NOT_LOADED
