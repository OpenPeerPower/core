"""Tests for the ATAG integration."""
from unittest.mock import patch

import aiohttp

from openpeerpower.components.atag import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_RETRY
from openpeerpower.core import OpenPeerPower

from tests.components.atag import init_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test configuration entry not ready on library error."""
    aioclient_mock.post("http://127.0.0.1:10000/retrieve", exc=aiohttp.ClientError)
    entry = await init_integration(opp, aioclient_mock)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_config_entry_empty_reply(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test configuration entry not ready when library returns False."""
    with patch("pyatag.AtagOne.update", return_value=False):
        entry = await init_integration(opp, aioclient_mock)
        assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the ATAG configuration entry unloading."""
    entry = await init_integration(opp, aioclient_mock)
    assert opp.data[DOMAIN]
    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
    assert not opp.data.get(DOMAIN)
