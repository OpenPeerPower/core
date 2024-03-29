"""The lock tests for the Mazda Connected Services integration."""

from openpeerpower.components.lock import (
    DOMAIN as LOCK_DOMAIN,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    STATE_LOCKED,
)
from openpeerpower.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME
from openpeerpower.helpers import entity_registry as er

from tests.components.mazda import init_integration


async def test_lock_setup(opp):
    """Test locking and unlocking the vehicle."""
    await init_integration(opp)

    entity_registry = er.async_get(opp)
    entry = entity_registry.async_get("lock.my_mazda3_lock")
    assert entry
    assert entry.unique_id == "JM000000000000000"

    state = opp.states.get("lock.my_mazda3_lock")
    assert state
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "My Mazda3 Lock"

    assert state.state == STATE_LOCKED


async def test_locking(opp):
    """Test locking the vehicle."""
    client_mock = await init_integration(opp)

    await opp.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {ATTR_ENTITY_ID: "lock.my_mazda3_lock"},
        blocking=True,
    )
    await opp.async_block_till_done()

    client_mock.lock_doors.assert_called_once()


async def test_unlocking(opp):
    """Test unlocking the vehicle."""
    client_mock = await init_integration(opp)

    await opp.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: "lock.my_mazda3_lock"},
        blocking=True,
    )
    await opp.async_block_till_done()

    client_mock.unlock_doors.assert_called_once()
