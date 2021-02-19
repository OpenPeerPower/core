"""The tests for the demo water_heater component."""
import pytest
import voluptuous as vol

from openpeerpower.components import water_heater
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util.unit_system import IMPERIAL_SYSTEM

from tests.components.water_heater import common

ENTITY_WATER_HEATER = "water_heater.demo_water_heater"
ENTITY_WATER_HEATER_CELSIUS = "water_heater.demo_water_heater_celsius"


@pytest.fixture(autouse=True)
async def setup_comp.opp):
    """Set up demo component."""
   .opp.config.units = IMPERIAL_SYSTEM
    assert await async_setup_component(
       .opp, water_heater.DOMAIN, {"water_heater": {"platform": "demo"}}
    )
    await.opp.async_block_till_done()


async def test_setup_params.opp):
    """Test the initial parameters."""
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") == 119
    assert state.attributes.get("away_mode") == "off"
    assert state.attributes.get("operation_mode") == "eco"


async def test_default_setup_params.opp):
    """Test the setup with default parameters."""
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("min_temp") == 110
    assert state.attributes.get("max_temp") == 140


async def test_set_only_target_temp_bad_attr.opp):
    """Test setting the target temperature without required attribute."""
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") == 119
    with pytest.raises(vol.Invalid):
        await common.async_set_temperature.opp, None, ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") == 119


async def test_set_only_target_temp.opp):
    """Test the setting of the target temperature."""
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") == 119
    await common.async_set_temperature.opp, 110, ENTITY_WATER_HEATER)
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") == 110


async def test_set_operation_bad_attr_and_state.opp):
    """Test setting operation mode without required attribute.

    Also check the state.
    """
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("operation_mode") == "eco"
    assert state.state == "eco"
    with pytest.raises(vol.Invalid):
        await common.async_set_operation_mode.opp, None, ENTITY_WATER_HEATER)
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("operation_mode") == "eco"
    assert state.state == "eco"


async def test_set_operation.opp):
    """Test setting of new operation mode."""
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("operation_mode") == "eco"
    assert state.state == "eco"
    await common.async_set_operation_mode.opp, "electric", ENTITY_WATER_HEATER)
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("operation_mode") == "electric"
    assert state.state == "electric"


async def test_set_away_mode_bad_attr.opp):
    """Test setting the away mode without required attribute."""
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("away_mode") == "off"
    with pytest.raises(vol.Invalid):
        await common.async_set_away_mode.opp, None, ENTITY_WATER_HEATER)
    assert state.attributes.get("away_mode") == "off"


async def test_set_away_mode_on.opp):
    """Test setting the away mode on/true."""
    await common.async_set_away_mode.opp, True, ENTITY_WATER_HEATER)
    state =.opp.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("away_mode") == "on"


async def test_set_away_mode_off.opp):
    """Test setting the away mode off/false."""
    await common.async_set_away_mode.opp, False, ENTITY_WATER_HEATER_CELSIUS)
    state =.opp.states.get(ENTITY_WATER_HEATER_CELSIUS)
    assert state.attributes.get("away_mode") == "off"


async def test_set_only_target_temp_with_convert.opp):
    """Test the setting of the target temperature."""
    state =.opp.states.get(ENTITY_WATER_HEATER_CELSIUS)
    assert state.attributes.get("temperature") == 113
    await common.async_set_temperature.opp, 114, ENTITY_WATER_HEATER_CELSIUS)
    state =.opp.states.get(ENTITY_WATER_HEATER_CELSIUS)
    assert state.attributes.get("temperature") == 114
