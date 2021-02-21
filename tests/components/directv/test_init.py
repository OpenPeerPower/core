"""Tests for the DirecTV integration."""
from openpeerpower.components.directv.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from tests.components.directv import setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker

# pylint: disable=redefined-outer-name


async def test_config_entry_not_ready(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the DirecTV configuration entry not ready."""
    entry = await setup_integration.opp, aioclient_mock, setup_error=True)

    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the DirecTV configuration entry unloading."""
    entry = await setup_integration.opp, aioclient_mock)

    assert entry.entry_id in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_LOADED

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()

    assert entry.entry_id not in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_NOT_LOADED
