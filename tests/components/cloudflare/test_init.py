"""Test the Cloudflare integration."""
from pycfdns.exceptions import CloudflareConnectionException

from openpeerpower.components.cloudflare.const import DOMAIN, SERVICE_UPDATE_RECORDS
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)

from . import ENTRY_CONFIG, init_integration

from tests.common import MockConfigEntry


async def test_unload_entry.opp, cfupdate):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not.opp.data.get(DOMAIN)


async def test_async_setup_raises_entry_not_ready.opp, cfupdate):
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    instance = cfupdate.return_value

    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to.opp.opp)

    instance.get_zone_id.side_effect = CloudflareConnectionException()
    await opp.config_entries.async_setup(entry.entry_id)

    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_integration_services.opp, cfupdate):
    """Test integration services."""
    instance = cfupdate.return_value

    entry = await init_integration.opp)
    assert entry.state == ENTRY_STATE_LOADED

    await opp.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_RECORDS,
        {},
        blocking=True,
    )
    await opp.async_block_till_done()

    instance.update_records.assert_called_once()
