"""Test cases around the demo fan platform."""
import pytest

from openpeerpower.components import fan
from openpeerpower.components.demo.fan import (
    PRESET_MODE_AUTO,
    PRESET_MODE_ON,
    PRESET_MODE_SLEEP,
    PRESET_MODE_SMART,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpowerr.setup import async_setup_component

FULL_FAN_ENTITY_IDS = ["fan.living_room_fan", "fan.percentage_full_fan"]
FANS_WITH_PRESET_MODE_ONLY = ["fan.preset_only_limited_fan"]
LIMITED_AND_FULL_FAN_ENTITY_IDS = FULL_FAN_ENTITY_IDS + [
    "fan.ceiling_fan",
    "fan.percentage_limited_fan",
]
FANS_WITH_PRESET_MODES = FULL_FAN_ENTITY_IDS + [
    "fan.percentage_limited_fan",
]


@pytest.fixture(autouse=True)
async def setup_comp.opp):
    """Initialize components."""
    assert await async_setup_component.opp, fan.DOMAIN, {"fan": {"platform": "demo"}})
    await opp.async_block_till_done()


@pytest.mark.parametrize("fan_entity_id", LIMITED_AND_FULL_FAN_ENTITY_IDS)
async def test_turn_on.opp, fan_entity_id):
    """Test turning on the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON


@pytest.mark.parametrize("fan_entity_id", FULL_FAN_ENTITY_IDS)
async def test_turn_on_with_speed_and_percentage.opp, fan_entity_id):
    """Test turning on the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_SPEED: fan.SPEED_HIGH},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_HIGH
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_SPEED: fan.SPEED_MEDIUM},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_MEDIUM
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_SPEED: fan.SPEED_LOW},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_LOW
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_HIGH
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_MEDIUM
    assert state.attributes[fan.ATTR_PERCENTAGE] == 66

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_LOW
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_OFF
    assert state.attributes[fan.ATTR_PERCENTAGE] == 0


@pytest.mark.parametrize("fan_entity_id", FANS_WITH_PRESET_MODE_ONLY)
async def test_turn_on_with_preset_mode_only.opp, fan_entity_id):
    """Test turning on the device with a preset_mode and no speed setting."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_AUTO
    assert state.attributes[fan.ATTR_PRESET_MODES] == [
        PRESET_MODE_AUTO,
        PRESET_MODE_SMART,
        PRESET_MODE_SLEEP,
        PRESET_MODE_ON,
    ]

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_SMART},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_SMART

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PRESET_MODE] is None

    with pytest.raises(ValueError):
        await.opp.services.async_call(
            fan.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )
        await opp.async_block_till_done()

    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PRESET_MODE] is None


@pytest.mark.parametrize("fan_entity_id", FANS_WITH_PRESET_MODES)
async def test_turn_on_with_preset_mode_and_speed.opp, fan_entity_id):
    """Test turning on the device with a preset_mode and speed."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == PRESET_MODE_AUTO
    assert state.attributes[fan.ATTR_PERCENTAGE] is None
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_AUTO
    assert state.attributes[fan.ATTR_SPEED_LIST] == [
        fan.SPEED_OFF,
        fan.SPEED_LOW,
        fan.SPEED_MEDIUM,
        fan.SPEED_HIGH,
        PRESET_MODE_AUTO,
        PRESET_MODE_SMART,
        PRESET_MODE_SLEEP,
        PRESET_MODE_ON,
    ]
    assert state.attributes[fan.ATTR_PRESET_MODES] == [
        PRESET_MODE_AUTO,
        PRESET_MODE_SMART,
        PRESET_MODE_SLEEP,
        PRESET_MODE_ON,
    ]

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_HIGH
    assert state.attributes[fan.ATTR_PERCENTAGE] == 100
    assert state.attributes[fan.ATTR_PRESET_MODE] is None

    await.opp.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_SMART},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == PRESET_MODE_SMART
    assert state.attributes[fan.ATTR_PERCENTAGE] is None
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_SMART

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_OFF
    assert state.attributes[fan.ATTR_PERCENTAGE] == 0
    assert state.attributes[fan.ATTR_PRESET_MODE] is None

    with pytest.raises(ValueError):
        await.opp.services.async_call(
            fan.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )
        await opp.async_block_till_done()

    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_OFF
    assert state.attributes[fan.ATTR_PERCENTAGE] == 0
    assert state.attributes[fan.ATTR_PRESET_MODE] is None


@pytest.mark.parametrize("fan_entity_id", LIMITED_AND_FULL_FAN_ENTITY_IDS)
async def test_turn_off.opp, fan_entity_id):
    """Test turning off the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF


@pytest.mark.parametrize("fan_entity_id", LIMITED_AND_FULL_FAN_ENTITY_IDS)
async def test_turn_off_without_entity_id.opp, fan_entity_id):
    """Test turning off all fans."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_MATCH_ALL}, blocking=True
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF


@pytest.mark.parametrize("fan_entity_id", FULL_FAN_ENTITY_IDS)
async def test_set_direction.opp, fan_entity_id):
    """Test setting the direction of the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_DIRECTION,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_DIRECTION: fan.DIRECTION_REVERSE},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_DIRECTION] == fan.DIRECTION_REVERSE


@pytest.mark.parametrize("fan_entity_id", FULL_FAN_ENTITY_IDS)
async def test_set_speed.opp, fan_entity_id):
    """Test setting the speed of the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_SPEED: fan.SPEED_LOW},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_LOW


@pytest.mark.parametrize("fan_entity_id", FANS_WITH_PRESET_MODES)
async def test_set_preset_mode.opp, fan_entity_id):
    """Test setting the preset mode of the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_SPEED] == PRESET_MODE_AUTO
    assert state.attributes[fan.ATTR_PERCENTAGE] is None
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_AUTO


@pytest.mark.parametrize("fan_entity_id", LIMITED_AND_FULL_FAN_ENTITY_IDS)
async def test_set_preset_mode_invalid.opp, fan_entity_id):
    """Test setting a invalid preset mode for the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    with pytest.raises(ValueError):
        await.opp.services.async_call(
            fan.DOMAIN,
            fan.SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )
        await opp.async_block_till_done()

    with pytest.raises(ValueError):
        await.opp.services.async_call(
            fan.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )
        await opp.async_block_till_done()


@pytest.mark.parametrize("fan_entity_id", FULL_FAN_ENTITY_IDS)
async def test_set_percentage.opp, fan_entity_id):
    """Test setting the percentage speed of the device."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_SPEED] == fan.SPEED_LOW
    assert state.attributes[fan.ATTR_PERCENTAGE] == 33


@pytest.mark.parametrize("fan_entity_id", FULL_FAN_ENTITY_IDS)
async def test_oscillate.opp, fan_entity_id):
    """Test oscillating the fan."""
    state = opp.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert not state.attributes.get(fan.ATTR_OSCILLATING)

    await.opp.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_OSCILLATE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_OSCILLATING: True},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_OSCILLATING] is True

    await.opp.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_OSCILLATE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_OSCILLATING: False},
        blocking=True,
    )
    state = opp.states.get(fan_entity_id)
    assert state.attributes[fan.ATTR_OSCILLATING] is False


@pytest.mark.parametrize("fan_entity_id", LIMITED_AND_FULL_FAN_ENTITY_IDS)
async def test_is_on.opp, fan_entity_id):
    """Test is on service call."""
    assert not fan.is_on.opp, fan_entity_id)

    await.opp.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    assert fan.is_on.opp, fan_entity_id)
