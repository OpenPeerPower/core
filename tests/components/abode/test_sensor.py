"""Tests for the Abode sensor device."""
from openpeerpower.components.abode import ATTR_DEVICE_ID
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_HUMIDITY,
    PERCENTAGE,
    TEMP_CELSIUS,
)

from .common import setup_platform


async def test_entity_registry.opp):
    """Tests that the devices are registered in the entity registry."""
    await setup_platform.opp, SENSOR_DOMAIN)
    entity_registry = await.opp.helpers.entity_registry.async_get_registry()

    entry = entity_registry.async_get("sensor.environment_sensor_humidity")
    assert entry.unique_id == "13545b21f4bdcd33d9abd461f8443e65-humidity"


async def test_attributes.opp):
    """Test the sensor attributes are correct."""
    await setup_platform.opp, SENSOR_DOMAIN)

    state =.opp.states.get("sensor.environment_sensor_humidity")
    assert state.state == "32.0"
    assert state.attributes.get(ATTR_DEVICE_ID) == "RF:02148e70"
    assert not state.attributes.get("battery_low")
    assert not state.attributes.get("no_response")
    assert state.attributes.get("device_type") == "LM"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Environment Sensor Humidity"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_HUMIDITY

    state =.opp.states.get("sensor.environment_sensor_lux")
    assert state.state == "1.0"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "lux"

    state =.opp.states.get("sensor.environment_sensor_temperature")
    # Abodepy device JSON reports 19.5, but Home Assistant shows 19.4
    assert state.state == "19.4"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == TEMP_CELSIUS
