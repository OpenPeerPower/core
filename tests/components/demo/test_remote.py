"""The tests for the demo remote component."""
import pytest

import openpeerpower.components.remote as remote
from openpeerpower.components.remote import ATTR_COMMAND
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component

ENTITY_ID = "remote.remote_one"
SERVICE_SEND_COMMAND = "send_command"


@pytest.fixture(autouse=True)
async def setup_component.opp):
    """Initialize components."""
    assert await async_setup_component(
       .opp, remote.DOMAIN, {"remote": {"platform": "demo"}}
    )
    await.opp.async_block_till_done()


async def test_methods.opp):
    """Test if services call the entity methods as expected."""
    await.opp.services.async_call(
        remote.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}
    )
    await.opp.async_block_till_done()
    state = opp.states.get(ENTITY_ID)
    assert state.state == STATE_ON

    await.opp.services.async_call(
        remote.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID}
    )
    await.opp.async_block_till_done()
    state = opp.states.get(ENTITY_ID)
    assert state.state == STATE_OFF

    await.opp.services.async_call(
        remote.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}
    )
    await.opp.async_block_till_done()
    state = opp.states.get(ENTITY_ID)
    assert state.state == STATE_ON

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_COMMAND: ["test"],
    }

    await.opp.services.async_call(remote.DOMAIN, SERVICE_SEND_COMMAND, data)
    await.opp.async_block_till_done()
    state = opp.states.get(ENTITY_ID)
    assert state.attributes == {
        "friendly_name": "Remote One",
        "last_command_sent": "test",
        "supported_features": 0,
    }
