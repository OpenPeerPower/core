"""Test the Met integration init."""
from openpeerpower.components.met.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_LOADED, ENTRY_STATE_NOT_LOADED

from . import init_integration


async def test_unload_entry.opp):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not opp.data.get(DOMAIN)
