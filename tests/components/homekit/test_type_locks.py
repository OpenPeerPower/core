"""Test different accessory types: Locks."""
import pytest

from openpeerpower.components.homekit.const import ATTR_VALUE
from openpeerpower.components.homekit.type_locks import Lock
from openpeerpower.components.lock import DOMAIN
from openpeerpower.const import (
    ATTR_CODE,
    ATTR_ENTITY_ID,
    STATE_LOCKED,
    STATE_UNKNOWN,
    STATE_UNLOCKED,
)

from tests.common import async_mock_service


async def test_lock_unlock(opp, hk_driver, events):
    """Test if accessory and HA are updated accordingly."""
    code = "1234"
    config = {ATTR_CODE: code}
    entity_id = "lock.kitchen_door"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Lock.opp, hk_driver, "Lock", entity_id, 2, config)
    await acc.run()

    assert acc.aid == 2
    assert acc.category == 6  # DoorLock

    assert acc.char_current_state.value == 3
    assert acc.char_target_state.value == 1

    opp.states.async_set(entity_id, STATE_LOCKED)
    await opp.async_block_till_done()
    assert acc.char_current_state.value == 1
    assert acc.char_target_state.value == 1

    opp.states.async_set(entity_id, STATE_UNLOCKED)
    await opp.async_block_till_done()
    assert acc.char_current_state.value == 0
    assert acc.char_target_state.value == 0

    opp.states.async_set(entity_id, STATE_UNKNOWN)
    await opp.async_block_till_done()
    assert acc.char_current_state.value == 3
    assert acc.char_target_state.value == 0

    opp.states.async_remove(entity_id)
    await opp.async_block_till_done()
    assert acc.char_current_state.value == 3
    assert acc.char_target_state.value == 0

    # Set from HomeKit
    call_lock = async_mock_service(opp, DOMAIN, "lock")
    call_unlock = async_mock_service(opp, DOMAIN, "unlock")

    await opp.async_add_executor_job(acc.char_target_state.client_update_value, 1)
    await opp.async_block_till_done()
    assert call_lock
    assert call_lock[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_lock[0].data[ATTR_CODE] == code
    assert acc.char_target_state.value == 1
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    await opp.async_add_executor_job(acc.char_target_state.client_update_value, 0)
    await opp.async_block_till_done()
    assert call_unlock
    assert call_unlock[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_unlock[0].data[ATTR_CODE] == code
    assert acc.char_target_state.value == 0
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None


@pytest.mark.parametrize("config", [{}, {ATTR_CODE: None}])
async def test_no_code(opp, hk_driver, config, events):
    """Test accessory if lock doesn't require a code."""
    entity_id = "lock.kitchen_door"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = Lock.opp, hk_driver, "Lock", entity_id, 2, config)

    # Set from HomeKit
    call_lock = async_mock_service(opp, DOMAIN, "lock")

    await opp.async_add_executor_job(acc.char_target_state.client_update_value, 1)
    await opp.async_block_till_done()
    assert call_lock
    assert call_lock[0].data[ATTR_ENTITY_ID] == entity_id
    assert ATTR_CODE not in call_lock[0].data
    assert acc.char_target_state.value == 1
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None
