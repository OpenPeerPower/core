"""Tests for the Roku integration."""
from unittest.mock import patch

from openpeerpower.components.roku.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from tests.components.roku import setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Roku configuration entry not ready."""
    entry = await setup_integration.opp, aioclient_mock, error=True)

    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Roku configuration entry unloading."""
    with patch(
        "openpeerpower.components.roku.media_player.async_setup_entry",
        return_value=True,
    ), patch(
        "openpeerpower.components.roku.remote.async_setup_entry",
        return_value=True,
    ):
        entry = await setup_integration.opp, aioclient_mock)

    assert.opp.data[DOMAIN][entry.entry_id]
    assert entry.state == ENTRY_STATE_LOADED

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()

    assert entry.entry_id not in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_NOT_LOADED
