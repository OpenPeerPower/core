"""The tests for the Remote component, adapted from Light Test."""

import openpeerpower.components.remote as remote
from openpeerpower.components.remote import (
    ATTR_ALTERNATIVE,
    ATTR_COMMAND,
    ATTR_COMMAND_TYPE,
    ATTR_DELAY_SECS,
    ATTR_DEVICE,
    ATTR_NUM_REPEATS,
    ATTR_TIMEOUT,
    DOMAIN,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_PLATFORM,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)

from tests.common import async_mock_service

TEST_PLATFORM = {DOMAIN: {CONF_PLATFORM: "test"}}
SERVICE_SEND_COMMAND = "send_command"
SERVICE_LEARN_COMMAND = "learn_command"
SERVICE_DELETE_COMMAND = "delete_command"
ENTITY_ID = "entity_id_val"


async def test_is_on(opp):
    """Test is_on."""
    opp.states.async_set("remote.test", STATE_ON)
    assert remote.is_on(opp, "remote.test")

    opp.states.async_set("remote.test", STATE_OFF)
    assert not remote.is_on(opp, "remote.test")


async def test_turn_on(opp):
    """Test turn_on."""
    turn_on_calls = async_mock_service(opp, DOMAIN, SERVICE_TURN_ON)
    await opp.services.async_call(DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID})

    await opp.async_block_till_done()

    assert len(turn_on_calls) == 1
    call = turn_on_calls[-1]

    assert call.domain == DOMAIN


async def test_turn_off(opp):
    """Test turn_off."""
    turn_off_calls = async_mock_service(opp, DOMAIN, SERVICE_TURN_OFF)

    await opp.services.async_call(DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID})

    await opp.async_block_till_done()

    assert len(turn_off_calls) == 1
    call = turn_off_calls[-1]

    assert call.domain == DOMAIN
    assert call.service == SERVICE_TURN_OFF
    assert call.data[ATTR_ENTITY_ID] == ENTITY_ID


async def test_send_command(opp):
    """Test send_command."""
    send_command_calls = async_mock_service(opp, DOMAIN, SERVICE_SEND_COMMAND)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_DEVICE: "test_device",
        ATTR_COMMAND: ["test_command"],
        ATTR_NUM_REPEATS: "4",
        ATTR_DELAY_SECS: "0.6",
    }

    await opp.services.async_call(DOMAIN, SERVICE_SEND_COMMAND, data)

    await opp.async_block_till_done()

    assert len(send_command_calls) == 1
    call = send_command_calls[-1]

    assert call.domain == DOMAIN
    assert call.service == SERVICE_SEND_COMMAND
    assert call.data[ATTR_ENTITY_ID] == ENTITY_ID


async def test_learn_command(opp):
    """Test learn_command."""
    learn_command_calls = async_mock_service(opp, DOMAIN, SERVICE_LEARN_COMMAND)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_DEVICE: "test_device",
        ATTR_COMMAND: ["test_command"],
        ATTR_COMMAND_TYPE: "rf",
        ATTR_ALTERNATIVE: True,
        ATTR_TIMEOUT: 20,
    }
    await opp.services.async_call(DOMAIN, SERVICE_LEARN_COMMAND, data)

    await opp.async_block_till_done()

    assert len(learn_command_calls) == 1
    call = learn_command_calls[-1]

    assert call.domain == DOMAIN
    assert call.service == SERVICE_LEARN_COMMAND
    assert call.data[ATTR_ENTITY_ID] == ENTITY_ID


async def test_delete_command(opp):
    """Test delete_command."""
    delete_command_calls = async_mock_service(
        opp, remote.DOMAIN, SERVICE_DELETE_COMMAND
    )

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_DEVICE: "test_device",
        ATTR_COMMAND: ["test_command"],
    }

    await opp.services.async_call(DOMAIN, SERVICE_DELETE_COMMAND, data)

    await opp.async_block_till_done()

    assert len(delete_command_calls) == 1
    call = delete_command_calls[-1]

    assert call.domain == remote.DOMAIN
    assert call.service == SERVICE_DELETE_COMMAND
    assert call.data[ATTR_ENTITY_ID] == ENTITY_ID


async def test_deprecated_base_class(caplog):
    """Test deprecated base class."""

    class CustomRemote(remote.RemoteDevice):
        pass

    CustomRemote()
    assert "RemoteDevice is deprecated, modify CustomRemote" in caplog.text
