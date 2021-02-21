"""The tests for the wake on lan switch platform."""
import platform
import subprocess
from unittest.mock import patch

import pytest

import openpeerpower.components.switch as switch
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpowerr.setup import async_setup_component

from tests.common import async_mock_service


@pytest.fixture(autouse=True)
def mock_send_magic_packet():
    """Mock magic packet."""
    with patch("wakeonlan.send_magic_packet") as mock_send:
        yield mock_send


async def test_valid_hostname.opp):
    """Test with valid hostname."""
    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {
            "switch": {
                "platform": "wake_on_lan",
                "mac": "00-01-02-03-04-05",
                "host": "validhostname",
            }
        },
    )
    await.opp.async_block_till_done()

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=0):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        state = opp.states.get("switch.wake_on_lan")
        assert STATE_ON == state.state

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        state = opp.states.get("switch.wake_on_lan")
        assert STATE_ON == state.state


async def test_valid_hostname_windows.opp):
    """Test with valid hostname on windows."""
    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {
            "switch": {
                "platform": "wake_on_lan",
                "mac": "00-01-02-03-04-05",
                "host": "validhostname",
            }
        },
    )
    await.opp.async_block_till_done()

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=0), patch.object(
        platform, "system", return_value="Windows"
    ):
        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_ON == state.state


async def test_broadcast_config_ip_and_port.opp, mock_send_magic_packet):
    """Test with broadcast address and broadcast port config."""
    mac = "00-01-02-03-04-05"
    broadcast_address = "255.255.255.255"
    port = 999

    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {
            "switch": {
                "platform": "wake_on_lan",
                "mac": mac,
                "broadcast_address": broadcast_address,
                "broadcast_port": port,
            }
        },
    )
    await.opp.async_block_till_done()

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=0):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        mock_send_magic_packet.assert_called_with(
            mac, ip_address=broadcast_address, port=port
        )


async def test_broadcast_config_ip.opp, mock_send_magic_packet):
    """Test with only broadcast address."""

    mac = "00-01-02-03-04-05"
    broadcast_address = "255.255.255.255"

    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {
            "switch": {
                "platform": "wake_on_lan",
                "mac": mac,
                "broadcast_address": broadcast_address,
            }
        },
    )
    await.opp.async_block_till_done()

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=0):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        mock_send_magic_packet.assert_called_with(mac, ip_address=broadcast_address)


async def test_broadcast_config_port.opp, mock_send_magic_packet):
    """Test with only broadcast port config."""

    mac = "00-01-02-03-04-05"
    port = 999

    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {"switch": {"platform": "wake_on_lan", "mac": mac, "broadcast_port": port}},
    )
    await.opp.async_block_till_done()

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=0):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        mock_send_magic_packet.assert_called_with(mac, port=port)


async def test_off_script.opp):
    """Test with turn off script."""

    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {
            "switch": {
                "platform": "wake_on_lan",
                "mac": "00-01-02-03-04-05",
                "host": "validhostname",
                "turn_off": {"service": "shell_command.turn_off_target"},
            }
        },
    )
    await.opp.async_block_till_done()
    calls = async_mock_service.opp, "shell_command", "turn_off_target")

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=0):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        state = opp.states.get("switch.wake_on_lan")
        assert STATE_ON == state.state
        assert len(calls) == 0

    with patch.object(subprocess, "call", return_value=2):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        state = opp.states.get("switch.wake_on_lan")
        assert STATE_OFF == state.state
        assert len(calls) == 1


async def test_invalid_hostname_windows.opp):
    """Test with invalid hostname on windows."""

    assert await async_setup_component(
       .opp,
        switch.DOMAIN,
        {
            "switch": {
                "platform": "wake_on_lan",
                "mac": "00-01-02-03-04-05",
                "host": "invalidhostname",
            }
        },
    )
    await.opp.async_block_till_done()

    state = opp.states.get("switch.wake_on_lan")
    assert STATE_OFF == state.state

    with patch.object(subprocess, "call", return_value=2):

        await.opp.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.wake_on_lan"},
            blocking=True,
        )

        state = opp.states.get("switch.wake_on_lan")
        assert STATE_OFF == state.state
