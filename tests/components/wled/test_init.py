"""Tests for the WLED integration."""
from unittest.mock import MagicMock, patch

from wled import WLEDConnectionError

from openpeerpower.components.wled.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_RETRY
from openpeerpower.core import OpenPeerPower

from tests.components.wled import init_integration
from tests.test_util.aiohttp import AiohttpClientMocker


@patch("openpeerpower.components.wled.WLED.update", side_effect=WLEDConnectionError)
async def test_config_entry_not_ready(
    mock_update: MagicMock, opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the WLED configuration entry not ready."""
    entry = await init_integration(opp, aioclient_mock)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the WLED configuration entry unloading."""
    entry = await init_integration(opp, aioclient_mock)
    assert opp.data[DOMAIN]

    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
    assert not opp.data.get(DOMAIN)


async def test_setting_unique_id(opp, aioclient_mock):
    """Test we set unique ID if not set yet."""
    entry = await init_integration(opp, aioclient_mock)

    assert opp.data[DOMAIN]
    assert entry.unique_id == "aabbccddeeff"
