"""Test the Nightscout config flow."""
from unittest.mock import patch

from aiohttp import ClientError

from openpeerpower.components.nightscout.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_URL

from tests.common import MockConfigEntry
from tests.components.nightscout import init_integration


async def test_unload_entry.opp):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not.opp.data.get(DOMAIN)


async def test_async_setup_raises_entry_not_ready.opp):
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "https://some.url:1234"},
    )
    config_entry.add_to_opp.opp)

    with patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_server_status",
        side_effect=ClientError(),
    ):
        await.opp.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ENTRY_STATE_SETUP_RETRY
