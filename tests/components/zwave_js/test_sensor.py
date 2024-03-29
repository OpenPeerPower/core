"""Test the Z-Wave JS sensor platform."""
from openpeerpower.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    TEMP_CELSIUS,
)
from openpeerpower.helpers import entity_registry as er

from .common import (
    AIR_TEMPERATURE_SENSOR,
    ENERGY_SENSOR,
    HUMIDITY_SENSOR,
    ID_LOCK_CONFIG_PARAMETER_SENSOR,
    NOTIFICATION_MOTION_SENSOR,
    POWER_SENSOR,
)


async def test_numeric_sensor(opp, multisensor_6, integration):
    """Test the numeric sensor."""
    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert state
    assert state.state == "9.0"
    assert state.attributes["unit_of_measurement"] == TEMP_CELSIUS
    assert state.attributes["device_class"] == DEVICE_CLASS_TEMPERATURE

    state = opp.states.get(HUMIDITY_SENSOR)

    assert state
    assert state.state == "65.0"
    assert state.attributes["unit_of_measurement"] == "%"
    assert state.attributes["device_class"] == DEVICE_CLASS_HUMIDITY


async def test_energy_sensors(opp, hank_binary_switch, integration):
    """Test power and energy sensors."""
    state = opp.states.get(POWER_SENSOR)

    assert state
    assert state.state == "0.0"
    assert state.attributes["unit_of_measurement"] == POWER_WATT
    assert state.attributes["device_class"] == DEVICE_CLASS_POWER

    state = opp.states.get(ENERGY_SENSOR)

    assert state
    assert state.state == "0.16"
    assert state.attributes["unit_of_measurement"] == ENERGY_KILO_WATT_HOUR
    assert state.attributes["device_class"] == DEVICE_CLASS_ENERGY


async def test_disabled_notification_sensor(opp, multisensor_6, integration):
    """Test sensor is created from Notification CC and is disabled."""
    ent_reg = er.async_get(opp)
    entity_entry = ent_reg.async_get(NOTIFICATION_MOTION_SENSOR)

    assert entity_entry
    assert entity_entry.disabled
    assert entity_entry.disabled_by == er.DISABLED_INTEGRATION

    # Test enabling entity
    updated_entry = ent_reg.async_update_entity(
        entity_entry.entity_id, **{"disabled_by": None}
    )
    assert updated_entry != entity_entry
    assert updated_entry.disabled is False

    # reload integration and check if entity is correctly there
    await opp.config_entries.async_reload(integration.entry_id)
    await opp.async_block_till_done()

    state = opp.states.get(NOTIFICATION_MOTION_SENSOR)
    assert state.state == "Motion detection"
    assert state.attributes["value"] == 8


async def test_config_parameter_sensor(opp, lock_id_lock_as_id150, integration):
    """Test config parameter sensor is created."""
    ent_reg = er.async_get(opp)
    entity_entry = ent_reg.async_get(ID_LOCK_CONFIG_PARAMETER_SENSOR)
    assert entity_entry
    assert entity_entry.disabled
