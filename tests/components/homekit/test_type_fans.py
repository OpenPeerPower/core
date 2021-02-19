"""Test different accessory types: Fans."""

from pyhap.const import HAP_REPR_AID, HAP_REPR_CHARS, HAP_REPR_IID, HAP_REPR_VALUE

from openpeerpower.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    DOMAIN,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_SET_SPEED,
)
from openpeerpower.components.homekit.const import ATTR_VALUE
from openpeerpower.components.homekit.type_fans import Fan
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    EVENT_OPENPEERPOWER_START,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from openpeerpowerr.core import CoreState
from openpeerpowerr.helpers import entity_registry

from tests.common import async_mock_service


async def test_fan_basic.opp, hk_driver, events):
    """Test fan with char state."""
    entity_id = "fan.demo"

   .opp.states.async_set(entity_id, STATE_ON, {ATTR_SUPPORTED_FEATURES: 0})
    await.opp.async_block_till_done()
    acc = Fan.opp, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.aid == 1
    assert acc.category == 3  # Fan
    assert acc.char_active.value == 1

    # If there are no speed_list values, then HomeKit speed is unsupported
    assert acc.char_speed is None

    await acc.run_op.dler()
    await.opp.async_block_till_done()
    assert acc.char_active.value == 1

   .opp.states.async_set(entity_id, STATE_OFF, {ATTR_SUPPORTED_FEATURES: 0})
    await.opp.async_block_till_done()
    assert acc.char_active.value == 0

   .opp.states.async_set(entity_id, STATE_UNKNOWN)
    await.opp.async_block_till_done()
    assert acc.char_active.value == 0

   .opp.states.async_remove(entity_id)
    await.opp.async_block_till_done()
    assert acc.char_active.value == 0

    # Set from HomeKit
    call_turn_on = async_mock_service.opp, DOMAIN, "turn_on")
    call_turn_off = async_mock_service.opp, DOMAIN, "turn_off")

    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

   .opp.states.async_set(entity_id, STATE_ON)
    await.opp.async_block_till_done()

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None


async def test_fan_direction.opp, hk_driver, events):
    """Test fan with direction."""
    entity_id = "fan.demo"

   .opp.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_FEATURES: SUPPORT_DIRECTION, ATTR_DIRECTION: DIRECTION_FORWARD},
    )
    await.opp.async_block_till_done()
    acc = Fan.opp, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_direction.value == 0

    await acc.run_op.dler()
    await.opp.async_block_till_done()
    assert acc.char_direction.value == 0

   .opp.states.async_set(entity_id, STATE_ON, {ATTR_DIRECTION: DIRECTION_REVERSE})
    await.opp.async_block_till_done()
    assert acc.char_direction.value == 1

    # Set from HomeKit
    call_set_direction = async_mock_service.opp, DOMAIN, "set_direction")

    char_direction_iid = acc.char_direction.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_block_till_done()
    assert call_set_direction[0]
    assert call_set_direction[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[0].data[ATTR_DIRECTION] == DIRECTION_FORWARD
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == DIRECTION_FORWARD

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_add_executor_job(acc.char_direction.client_update_value, 1)
    await.opp.async_block_till_done()
    assert call_set_direction[1]
    assert call_set_direction[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[1].data[ATTR_DIRECTION] == DIRECTION_REVERSE
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == DIRECTION_REVERSE


async def test_fan_oscillate.opp, hk_driver, events):
    """Test fan with oscillate."""
    entity_id = "fan.demo"

   .opp.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_FEATURES: SUPPORT_OSCILLATE, ATTR_OSCILLATING: False},
    )
    await.opp.async_block_till_done()
    acc = Fan.opp, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_swing.value == 0

    await acc.run_op.dler()
    await.opp.async_block_till_done()
    assert acc.char_swing.value == 0

   .opp.states.async_set(entity_id, STATE_ON, {ATTR_OSCILLATING: True})
    await.opp.async_block_till_done()
    assert acc.char_swing.value == 1

    # Set from HomeKit
    call_oscillate = async_mock_service.opp, DOMAIN, "oscillate")

    char_swing_iid = acc.char_swing.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_add_executor_job(acc.char_swing.client_update_value, 0)
    await.opp.async_block_till_done()
    assert call_oscillate[0]
    assert call_oscillate[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[0].data[ATTR_OSCILLATING] is False
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is False

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_add_executor_job(acc.char_swing.client_update_value, 1)
    await.opp.async_block_till_done()
    assert call_oscillate[1]
    assert call_oscillate[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[1].data[ATTR_OSCILLATING] is True
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is True


async def test_fan_speed.opp, hk_driver, events):
    """Test fan with speed."""
    entity_id = "fan.demo"

   .opp.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: SUPPORT_SET_SPEED,
            ATTR_PERCENTAGE: 0,
        },
    )
    await.opp.async_block_till_done()
    acc = Fan.opp, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    # Initial value can be anything but 0. If it is 0, it might cause HomeKit to set the
    # speed to 100 when turning on a fan on a freshly booted up server.
    assert acc.char_speed.value != 0

    await acc.run_op.dler()
    await.opp.async_block_till_done()

   .opp.states.async_set(entity_id, STATE_ON, {ATTR_PERCENTAGE: 100})
    await.opp.async_block_till_done()
    assert acc.char_speed.value == 100

    # Set from HomeKit
    call_set_percentage = async_mock_service.opp, DOMAIN, "set_percentage")

    char_speed_iid = acc.char_speed.to_HAP()[HAP_REPR_IID]
    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_add_executor_job(acc.char_speed.client_update_value, 42)
    await.opp.async_block_till_done()
    assert acc.char_speed.value == 42
    assert acc.char_active.value == 1

    assert call_set_percentage[0]
    assert call_set_percentage[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[0].data[ATTR_PERCENTAGE] == 42
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == 42

    # Verify speed is preserved from off to on
   .opp.states.async_set(entity_id, STATE_OFF, {ATTR_PERCENTAGE: 42})
    await.opp.async_block_till_done()
    assert acc.char_speed.value == 42
    assert acc.char_active.value == 0

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_block_till_done()
    assert acc.char_speed.value == 42
    assert acc.char_active.value == 1


async def test_fan_set_all_one_shot.opp, hk_driver, events):
    """Test fan with speed."""
    entity_id = "fan.demo"

   .opp.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: SUPPORT_SET_SPEED
            | SUPPORT_OSCILLATE
            | SUPPORT_DIRECTION,
            ATTR_PERCENTAGE: 0,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await.opp.async_block_till_done()
    acc = Fan.opp, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    # Initial value can be anything but 0. If it is 0, it might cause HomeKit to set the
    # speed to 100 when turning on a fan on a freshly booted up server.
    assert acc.char_speed.value != 0
    await acc.run_op.dler()
    await.opp.async_block_till_done()

   .opp.states.async_set(
        entity_id,
        STATE_OFF,
        {
            ATTR_SUPPORTED_FEATURES: SUPPORT_SET_SPEED
            | SUPPORT_OSCILLATE
            | SUPPORT_DIRECTION,
            ATTR_PERCENTAGE: 0,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == STATE_OFF

    # Set from HomeKit
    call_set_percentage = async_mock_service.opp, DOMAIN, "set_percentage")
    call_oscillate = async_mock_service.opp, DOMAIN, "oscillate")
    call_set_direction = async_mock_service.opp, DOMAIN, "set_direction")
    call_turn_on = async_mock_service.opp, DOMAIN, "turn_on")
    call_turn_off = async_mock_service.opp, DOMAIN, "turn_off")

    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]
    char_direction_iid = acc.char_direction.to_HAP()[HAP_REPR_IID]
    char_swing_iid = acc.char_swing.to_HAP()[HAP_REPR_IID]
    char_speed_iid = acc.char_speed.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_block_till_done()
    assert not call_turn_on
    assert call_set_percentage[0]
    assert call_set_percentage[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[0].data[ATTR_PERCENTAGE] == 42
    assert call_oscillate[0]
    assert call_oscillate[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[0].data[ATTR_OSCILLATING] is True
    assert call_set_direction[0]
    assert call_set_direction[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[0].data[ATTR_DIRECTION] == DIRECTION_REVERSE
    assert len(events) == 3

    assert events[0].data[ATTR_VALUE] is True
    assert events[1].data[ATTR_VALUE] == DIRECTION_REVERSE
    assert events[2].data[ATTR_VALUE] == 42

   .opp.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: SUPPORT_SET_SPEED
            | SUPPORT_OSCILLATE
            | SUPPORT_DIRECTION,
            ATTR_PERCENTAGE: 0,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await.opp.async_block_till_done()

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    # Turn on should not be called if its already on
    # and we set a fan speed
    await.opp.async_block_till_done()
    assert len(events) == 6
    assert call_set_percentage[1]
    assert call_set_percentage[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[1].data[ATTR_PERCENTAGE] == 42
    assert call_oscillate[1]
    assert call_oscillate[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[1].data[ATTR_OSCILLATING] is True
    assert call_set_direction[1]
    assert call_set_direction[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[1].data[ATTR_DIRECTION] == DIRECTION_REVERSE

    assert events[-3].data[ATTR_VALUE] is True
    assert events[-2].data[ATTR_VALUE] == DIRECTION_REVERSE
    assert events[-1].data[ATTR_VALUE] == 42

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 0,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await.opp.async_block_till_done()

    assert len(events) == 7
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(call_set_percentage) == 2
    assert len(call_oscillate) == 2
    assert len(call_set_direction) == 2


async def test_fan_restore.opp, hk_driver, events):
    """Test setting up an entity from state in the event registry."""
   .opp.state = CoreState.not_running

    registry = await entity_registry.async_get_registry.opp)

    registry.async_get_or_create(
        "fan",
        "generic",
        "1234",
        suggested_object_id="simple",
    )
    registry.async_get_or_create(
        "fan",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={"speed_list": ["off", "low", "medium", "high"]},
        supported_features=SUPPORT_SET_SPEED | SUPPORT_OSCILLATE | SUPPORT_DIRECTION,
        device_class="mock-device-class",
    )

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START, {})
    await.opp.async_block_till_done()

    acc = Fan.opp, hk_driver, "Fan", "fan.simple", 2, None)
    assert acc.category == 3
    assert acc.char_active is not None
    assert acc.char_direction is None
    assert acc.char_speed is None
    assert acc.char_swing is None

    acc = Fan.opp, hk_driver, "Fan", "fan.all_info_set", 2, None)
    assert acc.category == 3
    assert acc.char_active is not None
    assert acc.char_direction is not None
    assert acc.char_speed is not None
    assert acc.char_swing is not None
