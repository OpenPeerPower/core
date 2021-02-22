"""Tests for emulated_kasa library bindings."""
import math
from unittest.mock import AsyncMock, Mock, patch

from openpeerpower.components import emulated_kasa
from openpeerpower.components.emulated_kasa.const import (
    CONF_POWER,
    CONF_POWER_ENTITY,
    DOMAIN,
)
from openpeerpower.components.fan import (
    ATTR_SPEED,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_SPEED,
)
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import (
    ATTR_CURRENT_POWER_W,
    DOMAIN as SWITCH_DOMAIN,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    CONF_ENTITIES,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component

ENTITY_SWITCH = "switch.ac"
ENTITY_SWITCH_NAME = "A/C"
ENTITY_SWITCH_POWER = 400.0
ENTITY_LIGHT = "light.bed_light"
ENTITY_LIGHT_NAME = "Bed Room Lights"
ENTITY_FAN = "fan.ceiling_fan"
ENTITY_FAN_NAME = "Ceiling Fan"
ENTITY_FAN_SPEED_LOW = 5
ENTITY_FAN_SPEED_MED = 10
ENTITY_FAN_SPEED_HIGH = 50
ENTITY_SENSOR = "sensor.outside_temperature"
ENTITY_SENSOR_NAME = "Power Sensor"

CONFIG = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SWITCH: {
                CONF_NAME: ENTITY_SWITCH_NAME,
                CONF_POWER: ENTITY_SWITCH_POWER,
            },
            ENTITY_LIGHT: {
                CONF_NAME: ENTITY_LIGHT_NAME,
                CONF_POWER_ENTITY: ENTITY_SENSOR,
            },
            ENTITY_FAN: {
                CONF_POWER: "{% if is_state_attr('"
                + ENTITY_FAN
                + "','speed', 'low') %} "
                + str(ENTITY_FAN_SPEED_LOW)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','speed', 'medium') %} "
                + str(ENTITY_FAN_SPEED_MED)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','speed', 'high') %} "
                + str(ENTITY_FAN_SPEED_HIGH)
                + "{% endif %}"
            },
        }
    }
}

CONFIG_SWITCH = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SWITCH: {
                CONF_NAME: ENTITY_SWITCH_NAME,
                CONF_POWER: ENTITY_SWITCH_POWER,
            },
        }
    }
}

CONFIG_SWITCH_NO_POWER = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SWITCH: {},
        }
    }
}

CONFIG_LIGHT = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_LIGHT: {
                CONF_NAME: ENTITY_LIGHT_NAME,
                CONF_POWER_ENTITY: ENTITY_SENSOR,
            },
        }
    }
}

CONFIG_FAN = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_FAN: {
                CONF_POWER: "{% if is_state_attr('"
                + ENTITY_FAN
                + "','speed', 'low') %} "
                + str(ENTITY_FAN_SPEED_LOW)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','speed', 'medium') %} "
                + str(ENTITY_FAN_SPEED_MED)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','speed', 'high') %} "
                + str(ENTITY_FAN_SPEED_HIGH)
                + "{% endif %}"
            },
        }
    }
}

CONFIG_SENSOR = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SENSOR: {CONF_NAME: ENTITY_SENSOR_NAME},
        }
    }
}


def nested_value(ndict, *keys):
    """Return a nested dict value  or None if it doesn't exist."""
    if len(keys) == 0:
        return ndict
    key = keys[0]
    if not isinstance(ndict, dict) or key not in ndict:
        return None
    return nested_value(ndict[key], *keys[1:])


async def test_setup_opp):
    """Test that devices are reported correctly."""
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component.opp, DOMAIN, CONFIG) is True


async def test_float.opp):
    """Test a configuration using a simple float."""
    config = CONFIG_SWITCH[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        opp,
        SWITCH_DOMAIN,
        {SWITCH_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component.opp, DOMAIN, CONFIG_SWITCH) is True
    await opp.async_block_till_done()
    await emulated_kasa.validate_configs.opp, config)

    # Turn switch on
    await opp.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )

    switch = opp.states.get(ENTITY_SWITCH)
    assert switch.state == STATE_ON

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()

    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SWITCH_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_SWITCH_POWER)

    # Turn off
    await opp.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SWITCH_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)


async def test_switch_power.opp):
    """Test a configuration using a simple float."""
    config = CONFIG_SWITCH_NO_POWER[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        opp,
        SWITCH_DOMAIN,
        {SWITCH_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component.opp, DOMAIN, CONFIG_SWITCH_NO_POWER) is True
    await opp.async_block_till_done()
    await emulated_kasa.validate_configs.opp, config)

    # Turn switch on
    await opp.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )

    switch = opp.states.get(ENTITY_SWITCH)
    assert switch.state == STATE_ON
    power = switch.attributes[ATTR_CURRENT_POWER_W]
    assert power == 100
    assert switch.name == "AC"

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()

    assert nested_value(plug, "system", "get_sysinfo", "alias") == "AC"
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, power)

   .opp.states.async_set(
        ENTITY_SWITCH,
        STATE_ON,
        attributes={ATTR_CURRENT_POWER_W: 120, ATTR_FRIENDLY_NAME: "AC"},
    )

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()

    assert nested_value(plug, "system", "get_sysinfo", "alias") == "AC"
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 120)

    # Turn off
    await opp.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == "AC"
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)


async def test_template.opp):
    """Test a configuration using a complex template."""
    config = CONFIG_FAN[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        opp, FAN_DOMAIN, {FAN_DOMAIN: {"platform": "demo"}}
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component.opp, DOMAIN, CONFIG_FAN) is True
    await opp.async_block_till_done()
    await emulated_kasa.validate_configs.opp, config)

    # Turn all devices on to known state
    await opp.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_SPEED: "low"},
        blocking=True,
    )

    fan = opp.states.get(ENTITY_FAN)
    assert fan.state == STATE_ON

    # Fan low:
    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_FAN_SPEED_LOW)

    # Fan High:
    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_SPEED: "high"},
        blocking=True,
    )
    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_FAN_SPEED_HIGH)

    # Fan off:
    await opp.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)


async def test_sensor.opp):
    """Test a configuration using a sensor in a template."""
    config = CONFIG_LIGHT[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        opp, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        opp,
        SENSOR_DOMAIN,
        {SENSOR_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component.opp, DOMAIN, CONFIG_LIGHT) is True
    await opp.async_block_till_done()
    await emulated_kasa.validate_configs.opp, config)

    await opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )
   .opp.states.async_set(ENTITY_SENSOR, 35)

    light = opp.states.get(ENTITY_LIGHT)
    assert light.state == STATE_ON
    sensor = opp.states.get(ENTITY_SENSOR)
    assert sensor.state == "35"

    # light
    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_LIGHT_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 35)

    # change power sensor
   .opp.states.async_set(ENTITY_SENSOR, 40)

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_LIGHT_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 40)

    # report 0 if device is off
    await opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_LIGHT_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)


async def test_sensor_state.opp):
    """Test a configuration using a sensor in a template."""
    config = CONFIG_SENSOR[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        opp,
        SENSOR_DOMAIN,
        {SENSOR_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component.opp, DOMAIN, CONFIG_SENSOR) is True
    await opp.async_block_till_done()
    await emulated_kasa.validate_configs.opp, config)

   .opp.states.async_set(ENTITY_SENSOR, 35)

    sensor = opp.states.get(ENTITY_SENSOR)
    assert sensor.state == "35"

    # sensor
    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SENSOR_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 35)

    # change power sensor
   .opp.states.async_set(ENTITY_SENSOR, 40)

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SENSOR_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 40)

    # report 0 if device is off
   .opp.states.async_set(ENTITY_SENSOR, 0)

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SENSOR_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)


async def test_multiple_devices.opp):
    """Test that devices are reported correctly."""
    config = CONFIG[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        opp, SWITCH_DOMAIN, {SWITCH_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        opp, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        opp, FAN_DOMAIN, {FAN_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        opp,
        SENSOR_DOMAIN,
        {SENSOR_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await emulated_kasa.async_setup_opp, CONFIG) is True
    await opp.async_block_till_done()
    await emulated_kasa.validate_configs.opp, config)

    # Turn all devices on to known state
    await opp.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )
   .opp.states.async_set(ENTITY_SENSOR, 35)
    await opp.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await opp.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_SPEED: "medium"},
        blocking=True,
    )

    # All of them should now be on
    switch = opp.states.get(ENTITY_SWITCH)
    assert switch.state == STATE_ON
    light = opp.states.get(ENTITY_LIGHT)
    assert light.state == STATE_ON
    sensor = opp.states.get(ENTITY_SENSOR)
    assert sensor.state == "35"
    fan = opp.states.get(ENTITY_FAN)
    assert fan.state == STATE_ON

    plug_it = emulated_kasa.get_plug_devices.opp, config)
    # switch
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SWITCH_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_SWITCH_POWER)

    # light
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_LIGHT_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 35)

    # fan
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_FAN_SPEED_MED)

    # No more devices
    assert next(plug_it, None) is None
