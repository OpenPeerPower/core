"""Tests for the IPP integration."""
from openpeerpower.components.ipp.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpowerr.core import OpenPeerPower

from tests.components.ipp import init_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the IPP configuration entry not ready."""
    entry = await init_integration.opp, aioclient_mock, conn_error=True)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the IPP configuration entry unloading."""
    entry = await init_integration.opp, aioclient_mock)

    assert.opp.data[DOMAIN]
    assert entry.entry_id in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_LOADED

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()

    assert entry.entry_id not in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_NOT_LOADED
