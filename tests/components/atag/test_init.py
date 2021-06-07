"""Tests for the ATAG integration."""

from openpeerpower.components.atag import DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.core import OpenPeerPower

from . import init_integration, mock_connection

from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test configuration entry not ready on library error."""
    mock_connection(aioclient_mock, conn_error=True)
    entry = await init_integration(opp, aioclient_mock)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the ATAG configuration entry unloading."""
    entry = await init_integration(opp, aioclient_mock)
    assert opp.data[DOMAIN]
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
    assert not opp.data.get(DOMAIN)
