"""Tests for the Roku integration."""
from unittest.mock import patch

from openpeerpower.components.roku.const import DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.core import OpenPeerPower

from tests.components.roku import setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Roku configuration entry not ready."""
    entry = await setup_integration(opp, aioclient_mock, error=True)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Roku configuration entry unloading."""
    with patch(
        "openpeerpower.components.roku.media_player.async_setup_entry",
        return_value=True,
    ), patch(
        "openpeerpower.components.roku.remote.async_setup_entry",
        return_value=True,
    ):
        entry = await setup_integration(opp, aioclient_mock)

    assert opp.data[DOMAIN][entry.entry_id]
    assert entry.state is ConfigEntryState.LOADED

    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.entry_id not in opp.data[DOMAIN]
    assert entry.state is ConfigEntryState.NOT_LOADED
