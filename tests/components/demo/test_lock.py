"""The tests for the Demo lock platform."""
import pytest

from openpeerpower.components.demo import DOMAIN
from openpeerpower.components.lock import (
    DOMAIN as LOCK_DOMAIN,
    SERVICE_LOCK,
    SERVICE_OPEN,
    SERVICE_UNLOCK,
    STATE_LOCKED,
    STATE_UNLOCKED,
)
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.setup import async_setup_component

from tests.common import async_mock_service

FRONT = "lock.front_door"
KITCHEN = "lock.kitchen_door"
OPENABLE_LOCK = "lock.openable_lock"


@pytest.fixture(autouse=True)
async def setup_comp.opp):
    """Set up demo component."""
    assert await async_setup_component(
       .opp, LOCK_DOMAIN, {LOCK_DOMAIN: {"platform": DOMAIN}}
    )
    await.opp.async_block_till_done()


async def test_locking.opp):
    """Test the locking of a lock."""
    state =.opp.states.get(KITCHEN)
    assert state.state == STATE_UNLOCKED

    await.opp.services.async_call(
        LOCK_DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: KITCHEN}, blocking=True
    )

    state =.opp.states.get(KITCHEN)
    assert state.state == STATE_LOCKED


async def test_unlocking.opp):
    """Test the unlocking of a lock."""
    state =.opp.states.get(FRONT)
    assert state.state == STATE_LOCKED

    await.opp.services.async_call(
        LOCK_DOMAIN, SERVICE_UNLOCK, {ATTR_ENTITY_ID: FRONT}, blocking=True
    )

    state =.opp.states.get(FRONT)
    assert state.state == STATE_UNLOCKED


async def test_opening.opp):
    """Test the opening of a lock."""
    calls = async_mock_service.opp, LOCK_DOMAIN, SERVICE_OPEN)
    await.opp.services.async_call(
        LOCK_DOMAIN, SERVICE_OPEN, {ATTR_ENTITY_ID: OPENABLE_LOCK}, blocking=True
    )
    assert len(calls) == 1
