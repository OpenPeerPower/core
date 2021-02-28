"""The tests for the demo humidifier component."""

import pytest
import voluptuous as vol

from openpeerpower.components.humidifier.const import (
    ATTR_HUMIDITY,
    ATTR_MAX_HUMIDITY,
    ATTR_MIN_HUMIDITY,
    ATTR_MODE,
    DOMAIN,
    MODE_AWAY,
    MODE_ECO,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component

ENTITY_DEHUMIDIFIER = "humidifier.dehumidifier"
ENTITY_HYGROSTAT = "humidifier.hygrostat"
ENTITY_HUMIDIFIER = "humidifier.humidifier"


@pytest.fixture(autouse=True)
async def setup_demo_humidifier(opp):
    """Initialize setup demo humidifier."""
    assert await async_setup_component(
        opp. DOMAIN, {"humidifier": {"platform": "demo"}}
    )
    await opp.async_block_till_done()


def test_setup_params(opp):
    """Test the initial parameters."""
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_HUMIDITY) == 54


def test_default_setup_params(opp):
    """Test the setup with default parameters."""
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.attributes.get(ATTR_MIN_HUMIDITY) == 0
    assert state.attributes.get(ATTR_MAX_HUMIDITY) == 100


async def test_set_target_humidity_bad_attr(opp):
    """Test setting the target humidity without required attribute."""
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.attributes.get(ATTR_HUMIDITY) == 54

    with pytest.raises(vol.Invalid):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            {ATTR_HUMIDITY: None, ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
            blocking=True,
        )
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.attributes.get(ATTR_HUMIDITY) == 54


async def test_set_target_humidity(opp):
    """Test the setting of the target humidity."""
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.attributes.get(ATTR_HUMIDITY) == 54

    await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_HUMIDITY: 64, ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.attributes.get(ATTR_HUMIDITY) == 64


async def test_set_hold_mode_away(opp):
    """Test setting the hold mode away."""
    await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_MODE: MODE_AWAY, ATTR_ENTITY_ID: ENTITY_HYGROSTAT},
        blocking=True,
    )
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_HYGROSTAT)
    assert state.attributes.get(ATTR_MODE) == MODE_AWAY


async def test_set_hold_mode_eco(opp):
    """Test setting the hold mode eco."""
    await opp.services.async_call(
        DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_MODE: MODE_ECO, ATTR_ENTITY_ID: ENTITY_HYGROSTAT},
        blocking=True,
    )
    await opp.async_block_till_done()

    state = opp.states.get(ENTITY_HYGROSTAT)
    assert state.attributes.get(ATTR_MODE) == MODE_ECO


async def test_turn_on(opp):
    """Test turn on device."""
    await opp.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_OFF

    await opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_ON


async def test_turn_off(opp):
    """Test turn off device."""
    await opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_ON

    await opp.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_OFF


async def test_toggle(opp):
    """Test toggle device."""
    await opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_ON

    await opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_OFF

    await opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER}, blocking=True
    )
    state = opp.states.get(ENTITY_DEHUMIDIFIER)
    assert state.state == STATE_ON
