"""The tests for the group cover platform."""
from datetime import timedelta

import pytest

from openpeerpower.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DOMAIN,
)
from openpeerpower.components.group.cover import DEFAULT_NAME
from openpeerpower.const import (
    ATTR_ASSUMED_STATE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    CONF_ENTITIES,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_STOP_COVER_TILT,
    SERVICE_TOGGLE,
    SERVICE_TOGGLE_COVER_TILT,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed

COVER_GROUP = "cover.cover_group"
DEMO_COVER = "cover.kitchen_window"
DEMO_COVER_POS = "cover.hall_window"
DEMO_COVER_TILT = "cover.living_room_window"
DEMO_TILT = "cover.tilt_demo"

CONFIG_ALL = {
    DOMAIN: [
        {"platform": "demo"},
        {
            "platform": "group",
            CONF_ENTITIES: [DEMO_COVER, DEMO_COVER_POS, DEMO_COVER_TILT, DEMO_TILT],
        },
    ]
}

CONFIG_POS = {
    DOMAIN: [
        {"platform": "demo"},
        {
            "platform": "group",
            CONF_ENTITIES: [DEMO_COVER_POS, DEMO_COVER_TILT, DEMO_TILT],
        },
    ]
}

CONFIG_TILT_ONLY = {
    DOMAIN: [
        {"platform": "demo"},
        {
            "platform": "group",
            CONF_ENTITIES: [DEMO_COVER_TILT, DEMO_TILT],
        },
    ]
}

CONFIG_ATTRIBUTES = {
    DOMAIN: {
        "platform": "group",
        CONF_ENTITIES: [DEMO_COVER, DEMO_COVER_POS, DEMO_COVER_TILT, DEMO_TILT],
    }
}


@pytest.fixture
async def setup_comp.opp, config_count):
    """Set up group cover component."""
    config, count = config_count
    with assert_setup_component(count, DOMAIN):
        await async_setup_component.opp, DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()


@pytest.mark.parametrize("config_count", [(CONFIG_ATTRIBUTES, 1)])
async def test_attributes.opp, setup_comp):
    """Test handling of state attributes."""
    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_CLOSED
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert state.attributes[ATTR_ENTITY_ID] == [
        DEMO_COVER,
        DEMO_COVER_POS,
        DEMO_COVER_TILT,
        DEMO_TILT,
    ]
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports open / close / stop
   .opp.states.async_set(DEMO_COVER, STATE_OPEN, {ATTR_SUPPORTED_FEATURES: 11})
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 11
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports set_cover_position
   .opp.states.async_set(
        DEMO_COVER_POS,
        STATE_OPEN,
        {ATTR_SUPPORTED_FEATURES: 4, ATTR_CURRENT_POSITION: 70},
    )
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 15
    assert state.attributes[ATTR_CURRENT_POSITION] == 70
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports open tilt / close tilt / stop tilt
   .opp.states.async_set(DEMO_TILT, STATE_OPEN, {ATTR_SUPPORTED_FEATURES: 112})
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 127
    assert state.attributes[ATTR_CURRENT_POSITION] == 70
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

    # Add Entity that supports set_tilt_position
   .opp.states.async_set(
        DEMO_COVER_TILT,
        STATE_OPEN,
        {ATTR_SUPPORTED_FEATURES: 128, ATTR_CURRENT_TILT_POSITION: 60},
    )
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 255
    assert state.attributes[ATTR_CURRENT_POSITION] == 70
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

    # ### Test assumed state ###
    # ##########################

    # For covers
   .opp.states.async_set(
        DEMO_COVER, STATE_OPEN, {ATTR_SUPPORTED_FEATURES: 4, ATTR_CURRENT_POSITION: 100}
    )
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_ASSUMED_STATE] is True
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 244
    assert state.attributes[ATTR_CURRENT_POSITION] == 100
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

   .opp.states.async_remove(DEMO_COVER)
   .opp.states.async_remove(DEMO_COVER_POS)
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 240
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

    # For tilts
   .opp.states.async_set(
        DEMO_TILT,
        STATE_OPEN,
        {ATTR_SUPPORTED_FEATURES: 128, ATTR_CURRENT_TILT_POSITION: 100},
    )
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_ASSUMED_STATE] is True
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 128
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

   .opp.states.async_remove(DEMO_COVER_TILT)
   .opp.states.async_set(DEMO_TILT, STATE_CLOSED)
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_CLOSED
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    assert ATTR_CURRENT_POSITION not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION not in state.attributes

   .opp.states.async_set(DEMO_TILT, STATE_CLOSED, {ATTR_ASSUMED_STATE: True})
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.attributes[ATTR_ASSUMED_STATE] is True


@pytest.mark.parametrize("config_count", [(CONFIG_TILT_ONLY, 2)])
async def test_cover_that_only_supports_tilt_removed.opp, setup_comp):
    """Test removing a cover that support tilt."""
   .opp.states.async_set(
        DEMO_COVER_TILT,
        STATE_OPEN,
        {ATTR_SUPPORTED_FEATURES: 128, ATTR_CURRENT_TILT_POSITION: 60},
    )
   .opp.states.async_set(
        DEMO_TILT,
        STATE_OPEN,
        {ATTR_SUPPORTED_FEATURES: 128, ATTR_CURRENT_TILT_POSITION: 60},
    )
    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert state.attributes[ATTR_ENTITY_ID] == [
        DEMO_COVER_TILT,
        DEMO_TILT,
    ]
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert ATTR_CURRENT_TILT_POSITION in state.attributes

   .opp.states.async_remove(DEMO_COVER_TILT)
   .opp.states.async_set(DEMO_TILT, STATE_CLOSED)
    await.opp.async_block_till_done()


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_open_covers.opp, setup_comp):
    """Test open cover function."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )

    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100

    assert.opp.states.get(DEMO_COVER).state == STATE_OPEN
    assert.opp.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 100
    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 100


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_close_covers.opp, setup_comp):
    """Test close cover function."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )

    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    assert.opp.states.get(DEMO_COVER).state == STATE_CLOSED
    assert.opp.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 0
    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 0


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_toggle_covers.opp, setup_comp):
    """Test toggle cover function."""
    # Start covers in open state
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN

    # Toggle will close covers
    await.opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0

    assert.opp.states.get(DEMO_COVER).state == STATE_CLOSED
    assert.opp.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 0
    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 0

    # Toggle again will open covers
    await.opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100

    assert.opp.states.get(DEMO_COVER).state == STATE_OPEN
    assert.opp.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 100
    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 100


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_stop_covers.opp, setup_comp):
    """Test stop cover function."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    await.opp.services.async_call(
        DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 100

    assert.opp.states.get(DEMO_COVER).state == STATE_OPEN
    assert.opp.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 20
    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 80


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_set_cover_position.opp, setup_comp):
    """Test set cover position function."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: COVER_GROUP, ATTR_POSITION: 50},
        blocking=True,
    )
    for _ in range(4):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    assert.opp.states.get(DEMO_COVER).state == STATE_CLOSED
    assert.opp.states.get(DEMO_COVER_POS).attributes[ATTR_CURRENT_POSITION] == 50
    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_POSITION] == 50


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_open_tilts.opp, setup_comp):
    """Test open tilt function."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(5):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    assert (
       .opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 100
    )


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_close_tilts.opp, setup_comp):
    """Test close tilt function."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(5):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 0


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_toggle_tilts.opp, setup_comp):
    """Test toggle tilt function."""
    # Start tilted open
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    assert (
       .opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 100
    )

    # Toggle will tilt closed
    await.opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 0

    # Toggle again will tilt open
    await.opp.services.async_call(
        DOMAIN, SERVICE_TOGGLE_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    assert (
       .opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 100
    )


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_stop_tilts.opp, setup_comp):
    """Test stop tilts function."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    await.opp.services.async_call(
        DOMAIN, SERVICE_STOP_COVER_TILT, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 60

    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 60


@pytest.mark.parametrize("config_count", [(CONFIG_ALL, 2)])
async def test_set_tilt_positions.opp, setup_comp):
    """Test set tilt position function."""
    await.opp.services.async_call(
        DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: COVER_GROUP, ATTR_TILT_POSITION: 80},
        blocking=True,
    )
    for _ in range(3):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    state =.opp.states.get(COVER_GROUP)
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 80

    assert.opp.states.get(DEMO_COVER_TILT).attributes[ATTR_CURRENT_TILT_POSITION] == 80


@pytest.mark.parametrize("config_count", [(CONFIG_POS, 2)])
async def test_is_opening_closing.opp, setup_comp):
    """Test is_opening property."""
    await.opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )
    await.opp.async_block_till_done()

    assert.opp.states.get(DEMO_COVER_POS).state == STATE_OPENING
    assert.opp.states.get(DEMO_COVER_TILT).state == STATE_OPENING
    assert.opp.states.get(COVER_GROUP).state == STATE_OPENING

    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    await.opp.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: COVER_GROUP}, blocking=True
    )

    assert.opp.states.get(DEMO_COVER_POS).state == STATE_CLOSING
    assert.opp.states.get(DEMO_COVER_TILT).state == STATE_CLOSING
    assert.opp.states.get(COVER_GROUP).state == STATE_CLOSING

   .opp.states.async_set(DEMO_COVER_POS, STATE_OPENING, {ATTR_SUPPORTED_FEATURES: 11})
    await.opp.async_block_till_done()

    assert.opp.states.get(DEMO_COVER_POS).state == STATE_OPENING
    assert.opp.states.get(COVER_GROUP).state == STATE_OPENING

   .opp.states.async_set(DEMO_COVER_POS, STATE_CLOSING, {ATTR_SUPPORTED_FEATURES: 11})
    await.opp.async_block_till_done()

    assert.opp.states.get(DEMO_COVER_POS).state == STATE_CLOSING
    assert.opp.states.get(COVER_GROUP).state == STATE_CLOSING
