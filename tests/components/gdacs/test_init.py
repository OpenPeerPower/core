"""Define tests for the GDACS general setup."""
from unittest.mock import patch

from openpeerpower.components.gdacs import DOMAIN, FEED


async def test_component_unload_config_entry.opp, config_entry):
    """Test that loading and unloading of a config entry works."""
    config_entry.add_to.opp.opp)
    with patch("aio_georss_gdacs.GdacsFeedManager.update") as mock_feed_manager_update:
        # Load config entry.
        assert await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()
        assert mock_feed_manager_update.call_count == 1
        assert.opp.data[DOMAIN][FEED][config_entry.entry_id] is not None
        # Unload config entry.
        assert await.opp.config_entries.async_unload(config_entry.entry_id)
        await.opp.async_block_till_done()
        assert.opp.data[DOMAIN][FEED].get(config_entry.entry_id) is None
