"""The sensor tests for the Mazda Connected Services integration."""

from openpeerpower.components.mazda.const import DOMAIN
from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    PERCENTAGE,
    PRESSURE_PSI,
)
from openpeerpowerr.util.unit_system import IMPERIAL_SYSTEM

from tests.components.mazda import init_integration


async def test_device_nickname.opp):
    """Test creation of the device when vehicle has a nickname."""
    await init_integration.opp, use_nickname=True)

    device_registry = await.opp.helpers.device_registry.async_get_registry()
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )

    assert reg_device.model == "2021 MAZDA3 2.5 S SE AWD"
    assert reg_device.manufacturer == "Mazda"
    assert reg_device.name == "My Mazda3"


async def test_device_no_nickname.opp):
    """Test creation of the device when vehicle has no nickname."""
    await init_integration.opp, use_nickname=False)

    device_registry = await.opp.helpers.device_registry.async_get_registry()
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )

    assert reg_device.model == "2021 MAZDA3 2.5 S SE AWD"
    assert reg_device.manufacturer == "Mazda"
    assert reg_device.name == "2021 MAZDA3 2.5 S SE AWD"


async def test_sensors.opp):
    """Test creation of the sensors."""
    await init_integration.opp)

    entity_registry = await.opp.helpers.entity_registry.async_get_registry()

    # Fuel Remaining Percentage
    state = opp.states.get("sensor.my_mazda3_fuel_remaining_percentage")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "My Mazda3 Fuel Remaining Percentage"
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:gas-station"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE
    assert state.state == "87.0"
    entry = entity_registry.async_get("sensor.my_mazda3_fuel_remaining_percentage")
    assert entry
    assert entry.unique_id == "JM000000000000000_fuel_remaining_percentage"

    # Fuel Distance Remaining
    state = opp.states.get("sensor.my_mazda3_fuel_distance_remaining")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME) == "My Mazda3 Fuel Distance Remaining"
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:gas-station"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == LENGTH_KILOMETERS
    assert state.state == "381"
    entry = entity_registry.async_get("sensor.my_mazda3_fuel_distance_remaining")
    assert entry
    assert entry.unique_id == "JM000000000000000_fuel_distance_remaining"

    # Odometer
    state = opp.states.get("sensor.my_mazda3_odometer")
    assert state
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Mazda3 Odometer"
    assert state.attributes.get(ATTR_ICON) == "mdi:speedometer"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == LENGTH_KILOMETERS
    assert state.state == "2796"
    entry = entity_registry.async_get("sensor.my_mazda3_odometer")
    assert entry
    assert entry.unique_id == "JM000000000000000_odometer"

    # Front Left Tire Pressure
    state = opp.states.get("sensor.my_mazda3_front_left_tire_pressure")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME) == "My Mazda3 Front Left Tire Pressure"
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:car-tire-alert"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PRESSURE_PSI
    assert state.state == "35"
    entry = entity_registry.async_get("sensor.my_mazda3_front_left_tire_pressure")
    assert entry
    assert entry.unique_id == "JM000000000000000_front_left_tire_pressure"

    # Front Right Tire Pressure
    state = opp.states.get("sensor.my_mazda3_front_right_tire_pressure")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "My Mazda3 Front Right Tire Pressure"
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:car-tire-alert"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PRESSURE_PSI
    assert state.state == "35"
    entry = entity_registry.async_get("sensor.my_mazda3_front_right_tire_pressure")
    assert entry
    assert entry.unique_id == "JM000000000000000_front_right_tire_pressure"

    # Rear Left Tire Pressure
    state = opp.states.get("sensor.my_mazda3_rear_left_tire_pressure")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME) == "My Mazda3 Rear Left Tire Pressure"
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:car-tire-alert"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PRESSURE_PSI
    assert state.state == "33"
    entry = entity_registry.async_get("sensor.my_mazda3_rear_left_tire_pressure")
    assert entry
    assert entry.unique_id == "JM000000000000000_rear_left_tire_pressure"

    # Rear Right Tire Pressure
    state = opp.states.get("sensor.my_mazda3_rear_right_tire_pressure")
    assert state
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME) == "My Mazda3 Rear Right Tire Pressure"
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:car-tire-alert"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PRESSURE_PSI
    assert state.state == "33"
    entry = entity_registry.async_get("sensor.my_mazda3_rear_right_tire_pressure")
    assert entry
    assert entry.unique_id == "JM000000000000000_rear_right_tire_pressure"


async def test_sensors_imperial_units.opp):
    """Test that the sensors work properly with imperial units."""
   .opp.config.units = IMPERIAL_SYSTEM

    await init_integration.opp)

    # Fuel Distance Remaining
    state = opp.states.get("sensor.my_mazda3_fuel_distance_remaining")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == LENGTH_MILES
    assert state.state == "237"

    # Odometer
    state = opp.states.get("sensor.my_mazda3_odometer")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == LENGTH_MILES
    assert state.state == "1737"
