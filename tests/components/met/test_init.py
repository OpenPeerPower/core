"""Test the Met integration init."""
from openpeerpower.components.met.const import (
    DEFAULT_HOME_LATITUDE,
    DEFAULT_HOME_LONGITUDE,
    DOMAIN,
)
from openpeerpower.config import async_process_op_core_config
from openpeerpower.config_entries import ConfigEntryState

from . import init_integration


async def test_unload_entry(opp):
    """Test successful unload of entry."""
    entry = await init_integration(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not opp.data.get(DOMAIN)


async def test_fail_default_home_entry(opp, caplog):
    """Test abort setup of default home location."""
    await async_process_op_core_config(
        opp,
        {"latitude": 52.3731339, "longitude": 4.8903147},
    )

    assert opp.config.latitude == DEFAULT_HOME_LATITUDE
    assert opp.config.longitude == DEFAULT_HOME_LONGITUDE

    entry = await init_integration(opp, track_home=True)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state is ConfigEntryState.SETUP_ERROR

    assert (
        "Skip setting up met.no integration; No Home location has been set"
        in caplog.text
    )
