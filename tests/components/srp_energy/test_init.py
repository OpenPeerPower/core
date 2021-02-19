"""Tests for Srp Energy component Init."""
from openpeerpower.components import srp_energy

from tests.components.srp_energy import init_integration


async def test_setup_entry.opp):
    """Test setup entry fails if deCONZ is not available."""
    config_entry = await init_integration.opp)
    assert config_entry.state == "loaded"
    assert.opp.data[srp_energy.SRP_ENERGY_DOMAIN]


async def test_unload_entry.opp):
    """Test being able to unload an entry."""
    config_entry = await init_integration.opp)
    assert.opp.data[srp_energy.SRP_ENERGY_DOMAIN]

    assert await srp_energy.async_unload_entry.opp, config_entry)
    assert not.opp.data[srp_energy.SRP_ENERGY_DOMAIN]


async def test_async_setup_entry_with_exception.opp):
    """Test exception when SrpClient can't load."""
    await init_integration.opp, side_effect=Exception())
    assert srp_energy.SRP_ENERGY_DOMAIN not in.opp.data
