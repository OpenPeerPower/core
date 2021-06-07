"""
Test for Nest sensors platform for the Smart Device Management API.

These tests fake out the subscriber/devicemanager, and are not using a real
pubsub subscriber.
"""

from google_nest_sdm.device import Device
from google_nest_sdm.event import EventMessage

from openpeerpower.helpers import device_registry as dr, entity_registry as er

from .common import async_setup_sdm_platform

PLATFORM = "sensor"

THERMOSTAT_TYPE = "sdm.devices.types.THERMOSTAT"


async def async_setup_sensor(opp, devices={}, structures={}):
    """Set up the platform and prerequisites."""
    return await async_setup_sdm_platform(opp, PLATFORM, devices, structures)


async def test_thermostat_device(opp):
    """Test a thermostat with temperature and humidity sensors."""
    devices = {
        "some-device-id": Device.MakeDevice(
            {
                "name": "some-device-id",
                "type": THERMOSTAT_TYPE,
                "traits": {
                    "sdm.devices.traits.Info": {
                        "customName": "My Sensor",
                    },
                    "sdm.devices.traits.Temperature": {
                        "ambientTemperatureCelsius": 25.1,
                    },
                    "sdm.devices.traits.Humidity": {
                        "ambientHumidityPercent": 35.0,
                    },
                },
            },
            auth=None,
        )
    }
    await async_setup_sensor(opp, devices)

    temperature = opp.states.get("sensor.my_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "25.1"

    humidity = opp.states.get("sensor.my_sensor_humidity")
    assert humidity is not None
    assert humidity.state == "35.0"

    registry = er.async_get(opp)
    entry = registry.async_get("sensor.my_sensor_temperature")
    assert entry.unique_id == "some-device-id-temperature"
    assert entry.original_name == "My Sensor Temperature"
    assert entry.domain == "sensor"

    device_registry = dr.async_get(opp)
    device = device_registry.async_get(entry.device_id)
    assert device.name == "My Sensor"
    assert device.model == "Thermostat"
    assert device.identifiers == {("nest", "some-device-id")}


async def test_no_devices(opp):
    """Test no devices returned by the api."""
    await async_setup_sensor(opp)

    temperature = opp.states.get("sensor.my_sensor_temperature")
    assert temperature is None

    humidity = opp.states.get("sensor.my_sensor_humidity")
    assert humidity is None


async def test_device_no_sensor_traits(opp):
    """Test a device with applicable sensor traits."""
    devices = {
        "some-device-id": Device.MakeDevice(
            {
                "name": "some-device-id",
                "type": THERMOSTAT_TYPE,
                "traits": {},
            },
            auth=None,
        )
    }
    await async_setup_sensor(opp, devices)

    temperature = opp.states.get("sensor.my_sensor_temperature")
    assert temperature is None

    humidity = opp.states.get("sensor.my_sensor_humidity")
    assert humidity is None


async def test_device_name_from_structure(opp):
    """Test a device without a custom name, inferring name from structure."""
    devices = {
        "some-device-id": Device.MakeDevice(
            {
                "name": "some-device-id",
                "type": THERMOSTAT_TYPE,
                "traits": {
                    "sdm.devices.traits.Temperature": {
                        "ambientTemperatureCelsius": 25.2,
                    },
                },
                "parentRelations": [
                    {"parent": "some-structure-id", "displayName": "Some Room"}
                ],
            },
            auth=None,
        )
    }
    await async_setup_sensor(opp, devices)

    temperature = opp.states.get("sensor.some_room_temperature")
    assert temperature is not None
    assert temperature.state == "25.2"


async def test_event_updates_sensor(opp):
    """Test a pubsub message received by subscriber to update temperature."""
    devices = {
        "some-device-id": Device.MakeDevice(
            {
                "name": "some-device-id",
                "type": THERMOSTAT_TYPE,
                "traits": {
                    "sdm.devices.traits.Info": {
                        "customName": "My Sensor",
                    },
                    "sdm.devices.traits.Temperature": {
                        "ambientTemperatureCelsius": 25.1,
                    },
                },
            },
            auth=None,
        )
    }
    subscriber = await async_setup_sensor(opp, devices)

    temperature = opp.states.get("sensor.my_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "25.1"

    # Simulate a pubsub message received by the subscriber with a trait update
    event = EventMessage(
        {
            "eventId": "some-event-id",
            "timestamp": "2019-01-01T00:00:01Z",
            "resourceUpdate": {
                "name": "some-device-id",
                "traits": {
                    "sdm.devices.traits.Temperature": {
                        "ambientTemperatureCelsius": 26.2,
                    },
                },
            },
        },
        auth=None,
    )
    await subscriber.async_receive_event(event)
    await opp.async_block_till_done()  # Process dispatch/update signal

    temperature = opp.states.get("sensor.my_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "26.2"


async def test_device_with_unknown_type(opp):
    """Test a device without a custom name, inferring name from structure."""
    devices = {
        "some-device-id": Device.MakeDevice(
            {
                "name": "some-device-id",
                "type": "some-unknown-type",
                "traits": {
                    "sdm.devices.traits.Info": {
                        "customName": "My Sensor",
                    },
                    "sdm.devices.traits.Temperature": {
                        "ambientTemperatureCelsius": 25.1,
                    },
                },
            },
            auth=None,
        )
    }
    await async_setup_sensor(opp, devices)

    temperature = opp.states.get("sensor.my_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "25.1"

    registry = er.async_get(opp)
    entry = registry.async_get("sensor.my_sensor_temperature")
    assert entry.unique_id == "some-device-id-temperature"
    assert entry.original_name == "My Sensor Temperature"
    assert entry.domain == "sensor"

    device_registry = dr.async_get(opp)
    device = device_registry.async_get(entry.device_id)
    assert device.name == "My Sensor"
    assert device.model is None
    assert device.identifiers == {("nest", "some-device-id")}
