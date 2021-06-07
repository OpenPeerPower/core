"""Test the Kodi integration init."""
from unittest.mock import patch

from openpeerpower.components.kodi.const import DOMAIN
from openpeerpower.config_entries import ConfigEntryState

from . import init_integration


async def test_unload_entry(opp):
    """Test successful unload of entry."""
    with patch(
        "openpeerpower.components.kodi.media_player.async_setup_entry",
        return_value=True,
    ):
        entry = await init_integration(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not opp.data.get(DOMAIN)
