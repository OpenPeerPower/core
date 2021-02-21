"""The tests for the demo light component."""
import pytest

from openpeerpower.components.demo import DOMAIN
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_KELVIN,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_RGB_COLOR,
    ATTR_WHITE_VALUE,
    ATTR_XY_COLOR,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from openpeerpowerr.setup import async_setup_component

ENTITY_LIGHT = "light.bed_light"


@pytest.fixture(autouse=True)
async def setup_comp.opp):
    """Set up demo component."""
    assert await async_setup_component(
       .opp, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": DOMAIN}}
    )
    await opp.async_block_till_done()


async def test_state_attributes.opp):
    """Test light state attributes."""
    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_XY_COLOR: (0.4, 0.4), ATTR_BRIGHTNESS: 25},
        blocking=True,
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_XY_COLOR) == (0.4, 0.4)
    assert state.attributes.get(ATTR_BRIGHTNESS) == 25
    assert state.attributes.get(ATTR_RGB_COLOR) == (255, 234, 164)
    assert state.attributes.get(ATTR_EFFECT) == "rainbow"

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_RGB_COLOR: (251, 253, 255),
            ATTR_WHITE_VALUE: 254,
        },
        blocking=True,
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.attributes.get(ATTR_WHITE_VALUE) == 254
    assert state.attributes.get(ATTR_RGB_COLOR) == (250, 252, 255)
    assert state.attributes.get(ATTR_XY_COLOR) == (0.319, 0.326)

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_EFFECT: "none", ATTR_COLOR_TEMP: 400},
        blocking=True,
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.attributes.get(ATTR_COLOR_TEMP) == 400
    assert state.attributes.get(ATTR_MIN_MIREDS) == 153
    assert state.attributes.get(ATTR_MAX_MIREDS) == 500
    assert state.attributes.get(ATTR_EFFECT) == "none"

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_BRIGHTNESS_PCT: 50, ATTR_KELVIN: 3000},
        blocking=True,
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.attributes.get(ATTR_COLOR_TEMP) == 333
    assert state.attributes.get(ATTR_BRIGHTNESS) == 128


async def test_turn_off.opp):
    """Test light turn off method."""
    await.opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.state == STATE_ON

    await.opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.state == STATE_OFF


async def test_turn_off_without_entity_id.opp):
    """Test light turn off all lights."""
    await.opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: "all"}, blocking=True
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.state == STATE_ON

    await.opp.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "all"}, blocking=True
    )

    state = opp.states.get(ENTITY_LIGHT)
    assert state.state == STATE_OFF
