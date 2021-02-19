"""Axis binary sensor platform tests."""

from openpeerpower.components.axis.const import DOMAIN as AXIS_DOMAIN
from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpowerr.setup import async_setup_component

from .test_device import NAME, setup_axis_integration

EVENTS = [
    {
        "operation": "Initialized",
        "topic": "tns1:Device/tnsaxis:Sensor/PIR",
        "source": "sensor",
        "source_idx": "0",
        "type": "state",
        "value": "0",
    },
    {
        "operation": "Initialized",
        "topic": "tns1:PTZController/tnsaxis:PTZPresets/Channel_1",
        "source": "PresetToken",
        "source_idx": "0",
        "type": "on_preset",
        "value": "1",
    },
    {
        "operation": "Initialized",
        "topic": "tnsaxis:CameraApplicationPlatform/VMD/Camera1Profile1",
        "type": "active",
        "value": "1",
    },
]


async def test_platform_manually_configured.opp):
    """Test that nothing happens when platform is manually configured."""
    assert (
        await async_setup_component(
           .opp,
            BINARY_SENSOR_DOMAIN,
            {BINARY_SENSOR_DOMAIN: {"platform": AXIS_DOMAIN}},
        )
        is True
    )

    assert AXIS_DOMAIN not in.opp.data


async def test_no_binary_sensors.opp):
    """Test that no sensors in Axis results in no sensor entities."""
    await setup_axis_integration.opp)

    assert not.opp.states.async_entity_ids(BINARY_SENSOR_DOMAIN)


async def test_binary_sensors.opp):
    """Test that sensors are loaded properly."""
    config_entry = await setup_axis_integration.opp)
    device =.opp.data[AXIS_DOMAIN][config_entry.unique_id]

    device.api.event.update(EVENTS)
    await.opp.async_block_till_done()

    assert len.opp.states.async_entity_ids(BINARY_SENSOR_DOMAIN)) == 2

    pir =.opp.states.get(f"{BINARY_SENSOR_DOMAIN}.{NAME}_pir_0")
    assert pir.state == STATE_OFF
    assert pir.name == f"{NAME} PIR 0"
    assert pir.attributes["device_class"] == DEVICE_CLASS_MOTION

    vmd4 =.opp.states.get(f"{BINARY_SENSOR_DOMAIN}.{NAME}_vmd4_profile_1")
    assert vmd4.state == STATE_ON
    assert vmd4.name == f"{NAME} VMD4 Profile 1"
    assert vmd4.attributes["device_class"] == DEVICE_CLASS_MOTION
