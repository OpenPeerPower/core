"""Test init of GIOS integration."""
from unittest.mock import patch

from openpeerpower.components.gios.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import STATE_UNAVAILABLE

from tests.common import MockConfigEntry
from tests.components.gios import init_integration


async def test_async_setup_entry.opp):
    """Test a successful setup entry."""
    await init_integration.opp)

    state = opp.states.get("air_quality.home")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "4"


async def test_config_not_ready.opp):
    """Test for setup failure if connection to GIOS is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id=123,
        data={"station_id": 123, "name": "Home"},
    )

    with patch(
        "openpeerpower.components.gios.Gios._get_stations",
        side_effect=ConnectionError(),
    ):
        entry.add_to.opp.opp)
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_unload_entry.opp):
    """Test successful unload of entry."""
    entry = await init_integration.opp)

    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_NOT_LOADED
    assert not.opp.data.get(DOMAIN)
