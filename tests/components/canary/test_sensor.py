"""The tests for the Canary sensor platform."""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.components.canary.const import DOMAIN, MANUFACTURER
from openpeerpower.components.canary.sensor import (
    ATTR_AIR_QUALITY,
    STATE_AIR_QUALITY_ABNORMAL,
    STATE_AIR_QUALITY_NORMAL,
    STATE_AIR_QUALITY_VERY_ABNORMAL,
)
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    TEMP_CELSIUS,
)
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util.dt import utcnow

from . import mock_device, mock_location, mock_reading

from tests.common import async_fire_time_changed, mock_device_registry, mock_registry


async def test_sensors_pro.opp, canary) -> None:
    """Test the creation and values of the sensors for Canary Pro."""
    await async_setup_component.opp, "persistent_notification", {})

    registry = mock_registry.opp)
    device_registry = mock_device_registry.opp)

    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.59"),
    ]

    config = {DOMAIN: {"username": "test-username", "password": "test-password"}}
    with patch("openpeerpower.components.canary.PLATFORMS", ["sensor"]):
        assert await async_setup_component.opp, DOMAIN, config)
        await.opp.async_block_till_done()

    sensors = {
        "home_dining_room_temperature": (
            "20_temperature",
            "21.12",
            TEMP_CELSIUS,
            DEVICE_CLASS_TEMPERATURE,
            None,
        ),
        "home_dining_room_humidity": (
            "20_humidity",
            "50.46",
            PERCENTAGE,
            DEVICE_CLASS_HUMIDITY,
            None,
        ),
        "home_dining_room_air_quality": (
            "20_air_quality",
            "0.59",
            None,
            None,
            "mdi:weather-windy",
        ),
    }

    for (sensor_id, data) in sensors.items():
        entity_entry = registry.async_get(f"sensor.{sensor_id}")
        assert entity_entry
        assert entity_entry.device_class == data[3]
        assert entity_entry.unique_id == data[0]
        assert entity_entry.original_icon == data[4]

        state = opp.states.get(f"sensor.{sensor_id}")
        assert state
        assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == data[2]
        assert state.state == data[1]

    device = device_registry.async_get_device({(DOMAIN, "20")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "Dining Room"
    assert device.model == "Canary Pro"


async def test_sensors_attributes_pro.opp, canary) -> None:
    """Test the creation and values of the sensors attributes for Canary Pro."""
    await async_setup_component.opp, "persistent_notification", {})

    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.59"),
    ]

    config = {DOMAIN: {"username": "test-username", "password": "test-password"}}
    with patch("openpeerpower.components.canary.PLATFORMS", ["sensor"]):
        assert await async_setup_component.opp, DOMAIN, config)
        await.opp.async_block_till_done()

    entity_id = "sensor.home_dining_room_air_quality"
    state = opp.states.get(entity_id)
    assert state
    assert state.attributes[ATTR_AIR_QUALITY] == STATE_AIR_QUALITY_ABNORMAL

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.4"),
    ]

    future = utcnow() + timedelta(seconds=30)
    async_fire_time_changed.opp, future)
    await.opp.helpers.entity_component.async_update_entity(entity_id)
    await.opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.attributes[ATTR_AIR_QUALITY] == STATE_AIR_QUALITY_VERY_ABNORMAL

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "1.0"),
    ]

    future += timedelta(seconds=30)
    async_fire_time_changed.opp, future)
    await.opp.helpers.entity_component.async_update_entity(entity_id)
    await.opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.attributes[ATTR_AIR_QUALITY] == STATE_AIR_QUALITY_NORMAL


async def test_sensors_flex.opp, canary) -> None:
    """Test the creation and values of the sensors for Canary Flex."""
    await async_setup_component.opp, "persistent_notification", {})

    registry = mock_registry.opp)
    device_registry = mock_device_registry.opp)

    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Flex")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("battery", "70.4567"),
        mock_reading("wifi", "-57"),
    ]

    config = {DOMAIN: {"username": "test-username", "password": "test-password"}}
    with patch("openpeerpower.components.canary.PLATFORMS", ["sensor"]):
        assert await async_setup_component.opp, DOMAIN, config)
        await.opp.async_block_till_done()

    sensors = {
        "home_dining_room_battery": (
            "20_battery",
            "70.46",
            PERCENTAGE,
            DEVICE_CLASS_BATTERY,
            None,
        ),
        "home_dining_room_wifi": (
            "20_wifi",
            "-57.0",
            SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            DEVICE_CLASS_SIGNAL_STRENGTH,
            None,
        ),
    }

    for (sensor_id, data) in sensors.items():
        entity_entry = registry.async_get(f"sensor.{sensor_id}")
        assert entity_entry
        assert entity_entry.device_class == data[3]
        assert entity_entry.unique_id == data[0]
        assert entity_entry.original_icon == data[4]

        state = opp.states.get(f"sensor.{sensor_id}")
        assert state
        assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == data[2]
        assert state.state == data[1]

    device = device_registry.async_get_device({(DOMAIN, "20")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "Dining Room"
    assert device.model == "Canary Flex"
