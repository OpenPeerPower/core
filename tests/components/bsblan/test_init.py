"""Tests for the BSBLan integration."""
import aiohttp

from openpeerpower.components.bsblan.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_RETRY
from openpeerpowerr.core import OpenPeerPower

from tests.components.bsblan import init_integration, init_integration_without_auth
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the BSBLan configuration entry not ready."""
    aioclient_mock.post(
        "http://example.local:80/1234/JQ?Parameter=6224,6225,6226",
        exc=aiohttp.ClientError,
    )

    entry = await init_integration.opp, aioclient_mock)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_config_entry(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the BSBLan configuration entry unloading."""
    entry = await init_integration.opp, aioclient_mock)
    assert.opp.data[DOMAIN]

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()
    assert not.opp.data.get(DOMAIN)


async def test_config_entry_no_authentication(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the BSBLan configuration entry not ready."""
    aioclient_mock.post(
        "http://example.local:80/1234/JQ?Parameter=6224,6225,6226",
        exc=aiohttp.ClientError,
    )

    entry = await init_integration_without_auth.opp, aioclient_mock)
    assert entry.state == ENTRY_STATE_SETUP_RETRY
