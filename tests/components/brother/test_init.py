"""Test init of Brother integration."""
from unittest.mock import patch

from openpeerpower.components.brother.const import DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import CONF_HOST, CONF_TYPE, STATE_UNAVAILABLE

from tests.common import MockConfigEntry
from tests.components.brother import init_integration


async def test_async_setup_entry(opp):
    """Test a successful setup entry."""
    await init_integration(opp)

    state = opp.states.get("sensor.hl_l2340dw_status")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "waiting"


async def test_config_not_ready(opp):
    """Test for setup failure if connection to broker is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="HL-L2340DW 0123456789",
        unique_id="0123456789",
        data={CONF_HOST: "localhost", CONF_TYPE: "laser"},
    )

    with patch("brother.Brother._get_data", side_effect=ConnectionError()):
        entry.add_to_opp(opp)
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(opp):
    """Test successful unload of entry."""
    entry = await init_integration(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not opp.data.get(DOMAIN)
