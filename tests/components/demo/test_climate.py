"""The tests for the demo climate component."""

import pytest
import voluptuous as vol

from openpeerpower.components.climate.const import (
    ATTR_AUX_HEAT,
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_HUMIDITY,
    ATTR_MAX_TEMP,
    ATTR_MIN_HUMIDITY,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    CURRENT_HVAC_COOL,
    DOMAIN,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_ECO,
    SERVICE_SET_AUX_HEAT,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component
from openpeerpower.util.unit_system import METRIC_SYSTEM

ENTITY_CLIMATE = "climate.hvac"
ENTITY_ECOBEE = "climate.ecobee"
ENTITY_HEATPUMP = "climate.heatpump"


@pytest.fixture(autouse=True)
async def setup_demo_climate.opp):
    """Initialize setup demo climate."""
   .opp.config.units = METRIC_SYSTEM
    assert await async_setup_component.opp, DOMAIN, {"climate": {"platform": "demo"}})
    await.opp.async_block_till_done()


def test_setup_params.opp):
    """Test the initial parameters."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_COOL
    assert state.attributes.get(ATTR_TEMPERATURE) == 21
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 22
    assert state.attributes.get(ATTR_FAN_MODE) == "On High"
    assert state.attributes.get(ATTR_HUMIDITY) == 67
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 54
    assert state.attributes.get(ATTR_SWING_MODE) == "Off"
    assert STATE_OFF == state.attributes.get(ATTR_AUX_HEAT)
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        "off",
        "heat",
        "cool",
        "auto",
        "dry",
        "fan_only",
    ]


def test_default_setup_params.opp):
    """Test the setup with default parameters."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_MIN_TEMP) == 7
    assert state.attributes.get(ATTR_MAX_TEMP) == 35
    assert state.attributes.get(ATTR_MIN_HUMIDITY) == 30
    assert state.attributes.get(ATTR_MAX_HUMIDITY) == 99


async def test_set_only_target_temp_bad_attr.opp):
    """Test setting the target temperature without required attribute."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_TEMPERATURE) == 21

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_TEMPERATURE: None},
            blocking=True,
        )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_TEMPERATURE) == 21


async def test_set_only_target_temp.opp):
    """Test the setting of the target temperature."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_TEMPERATURE) == 21

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_TEMPERATURE: 30},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_TEMPERATURE) == 30.0


async def test_set_only_target_temp_with_convert.opp):
    """Test the setting of the target temperature."""
    state =.opp.states.get(ENTITY_HEATPUMP)
    assert state.attributes.get(ATTR_TEMPERATURE) == 20

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_HEATPUMP, ATTR_TEMPERATURE: 21},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_HEATPUMP)
    assert state.attributes.get(ATTR_TEMPERATURE) == 21.0


async def test_set_target_temp_range.opp):
    """Test the setting of the target temperature with range."""
    state =.opp.states.get(ENTITY_ECOBEE)
    assert state.attributes.get(ATTR_TEMPERATURE) is None
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 21.0
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 24.0

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: ENTITY_ECOBEE,
            ATTR_TARGET_TEMP_LOW: 20,
            ATTR_TARGET_TEMP_HIGH: 25,
        },
        blocking=True,
    )

    state =.opp.states.get(ENTITY_ECOBEE)
    assert state.attributes.get(ATTR_TEMPERATURE) is None
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 20.0
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 25.0


async def test_set_target_temp_range_bad_attr.opp):
    """Test setting the target temperature range without attribute."""
    state =.opp.states.get(ENTITY_ECOBEE)
    assert state.attributes.get(ATTR_TEMPERATURE) is None
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 21.0
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 24.0

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: ENTITY_ECOBEE,
                ATTR_TARGET_TEMP_LOW: None,
                ATTR_TARGET_TEMP_HIGH: None,
            },
            blocking=True,
        )

    state =.opp.states.get(ENTITY_ECOBEE)
    assert state.attributes.get(ATTR_TEMPERATURE) is None
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 21.0
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 24.0


async def test_set_target_humidity_bad_attr.opp):
    """Test setting the target humidity without required attribute."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_HUMIDITY) == 67

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HUMIDITY: None},
            blocking=True,
        )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_HUMIDITY) == 67


async def test_set_target_humidity.opp):
    """Test the setting of the target humidity."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_HUMIDITY) == 67

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HUMIDITY: 64},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_HUMIDITY) == 64.0


async def test_set_fan_mode_bad_attr.opp):
    """Test setting fan mode without required attribute."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_FAN_MODE) == "On High"

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_FAN_MODE: None},
            blocking=True,
        )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_FAN_MODE) == "On High"


async def test_set_fan_mode.opp):
    """Test setting of new fan mode."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_FAN_MODE) == "On High"

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_FAN_MODE: "On Low"},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_FAN_MODE) == "On Low"


async def test_set_swing_mode_bad_attr.opp):
    """Test setting swing mode without required attribute."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_SWING_MODE) == "Off"

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_SWING_MODE: None},
            blocking=True,
        )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_SWING_MODE) == "Off"


async def test_set_swing.opp):
    """Test setting of new swing mode."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_SWING_MODE) == "Off"

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_SWING_MODE: "Auto"},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_SWING_MODE) == "Auto"


async def test_set_hvac_bad_attr_and_state.opp):
    """Test setting hvac mode without required attribute.

    Also check the state.
    """
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_HVAC_ACTION) == CURRENT_HVAC_COOL
    assert state.state == HVAC_MODE_COOL

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: None},
            blocking=True,
        )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_HVAC_ACTION) == CURRENT_HVAC_COOL
    assert state.state == HVAC_MODE_COOL


async def test_set_hvac.opp):
    """Test setting of new hvac mode."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_COOL

    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: HVAC_MODE_HEAT},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_HEAT


async def test_set_hold_mode_away.opp):
    """Test setting the hold mode away."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ECOBEE, ATTR_PRESET_MODE: PRESET_AWAY},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_ECOBEE)
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_AWAY


async def test_set_hold_mode_eco.opp):
    """Test setting the hold mode eco."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ECOBEE, ATTR_PRESET_MODE: PRESET_ECO},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_ECOBEE)
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_ECO


async def test_set_aux_heat_bad_attr.opp):
    """Test setting the auxiliary heater without required attribute."""
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_AUX_HEAT) == STATE_OFF

    with pytest.raises(vol.Invalid):
        await.opp.services.async_call(
            DOMAIN,
            SERVICE_SET_AUX_HEAT,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_AUX_HEAT: None},
            blocking=True,
        )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_AUX_HEAT) == STATE_OFF


async def test_set_aux_heat_on.opp):
    """Test setting the axillary heater on/true."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_AUX_HEAT,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_AUX_HEAT: True},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_AUX_HEAT) == STATE_ON


async def test_set_aux_heat_off.opp):
    """Test setting the auxiliary heater off/false."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_AUX_HEAT,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_AUX_HEAT: False},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get(ATTR_AUX_HEAT) == STATE_OFF


async def test_turn_on.opp):
    """Test turn on device."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: HVAC_MODE_OFF},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_OFF

    await.opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_CLIMATE}, blocking=True
    )
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_HEAT


async def test_turn_off.opp):
    """Test turn on device."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: HVAC_MODE_HEAT},
        blocking=True,
    )

    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_HEAT

    await.opp.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_CLIMATE}, blocking=True
    )
    state =.opp.states.get(ENTITY_CLIMATE)
    assert state.state == HVAC_MODE_OFF
