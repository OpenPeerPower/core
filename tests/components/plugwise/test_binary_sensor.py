"""Tests for the Plugwise binary_sensor integration."""

from openpeerpower.config_entries import ENTRY_STATE_LOADED
from openpeerpower.const import STATE_OFF, STATE_ON

from tests.components.plugwise.common import async_init_integration


async def test_anna_climate_binary_sensor_entities.opp, mock_smile_anna):
    """Test creation of climate related binary_sensor entities."""
    entry = await async_init_integration.opp, mock_smile_anna)
    assert entry.state == ENTRY_STATE_LOADED

    state = opp.states.get("binary_sensor.auxiliary_slave_boiler_state")
    assert str(state.state) == STATE_OFF

    state = opp.states.get("binary_sensor.auxiliary_dhw_state")
    assert str(state.state) == STATE_OFF


async def test_anna_climate_binary_sensor_change.opp, mock_smile_anna):
    """Test change of climate related binary_sensor entities."""
    entry = await async_init_integration.opp, mock_smile_anna)
    assert entry.state == ENTRY_STATE_LOADED

   .opp.states.async_set("binary_sensor.auxiliary_dhw_state", STATE_ON, {})
    await opp..async_block_till_done()

    state = opp.states.get("binary_sensor.auxiliary_dhw_state")
    assert str(state.state) == STATE_ON

    await opp..helpers.entity_component.async_update_entity(
        "binary_sensor.auxiliary_dhw_state"
    )

    state = opp.states.get("binary_sensor.auxiliary_dhw_state")
    assert str(state.state) == STATE_OFF


async def test_adam_climate_binary_sensor_change.opp, mock_smile_adam):
    """Test change of climate related binary_sensor entities."""
    entry = await async_init_integration.opp, mock_smile_adam)
    assert entry.state == ENTRY_STATE_LOADED

    state = opp.states.get("binary_sensor.adam_plugwise_notification")
    assert str(state.state) == STATE_ON
    assert "unreachable" in state.attributes.get("warning_msg")[0]
    assert not state.attributes.get("error_msg")
    assert not state.attributes.get("other_msg")
