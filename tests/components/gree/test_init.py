"""Tests for the Gree Integration."""
from unittest.mock import patch

from openpeerpower.components.gree.const import DOMAIN as GREE_DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_setup_simple(opp):
    """Test gree integration is setup."""
    entry = MockConfigEntry(domain=GREE_DOMAIN)
    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.gree.climate.async_setup_entry",
        return_value=True,
    ) as climate_setup, patch(
        "openpeerpower.components.gree.switch.async_setup_entry",
        return_value=True,
    ) as switch_setup:
        assert await async_setup_component(opp, GREE_DOMAIN, {})
        await opp.async_block_till_done()

        assert len(climate_setup.mock_calls) == 1
        assert len(switch_setup.mock_calls) == 1
        assert entry.state is ConfigEntryState.LOADED

    # No flows started
    assert len(opp.config_entries.flow.async_progress()) == 0


async def test_unload_config_entry(opp):
    """Test that the async_unload_entry works."""
    # As we have currently no configuration, we just to pass the domain here.
    entry = MockConfigEntry(domain=GREE_DOMAIN)
    entry.add_to_opp(opp)

    assert await async_setup_component(opp, GREE_DOMAIN, {})
    await opp.async_block_till_done()

    await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
