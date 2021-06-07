"""The tests for the Command line switch platform."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.components.switch import DOMAIN, SCAN_INTERVAL
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import OpenPeerPower
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed


async def setup_test_entity(opp: OpenPeerPower, config_dict: dict[str, Any]) -> None:
    """Set up a test command line switch entity."""
    assert await setup.async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {"platform": "command_line", "switches": config_dict},
            ]
        },
    )
    await opp.async_block_till_done()


async def test_state_none(opp: OpenPeerPower) -> None:
    """Test with none state."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "switch_status")
        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_on": f"echo 1 > {path}",
                    "command_off": f"echo 0 > {path}",
                }
            },
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_ON

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF


async def test_state_value(opp: OpenPeerPower) -> None:
    """Test with state value."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "switch_status")
        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_state": f"cat {path}",
                    "command_on": f"echo 1 > {path}",
                    "command_off": f"echo 0 > {path}",
                    "value_template": '{{ value=="1" }}',
                }
            },
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_ON

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF


async def test_state_json_value(opp: OpenPeerPower) -> None:
    """Test with state JSON value."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "switch_status")
        oncmd = json.dumps({"status": "ok"})
        offcmd = json.dumps({"status": "nope"})

        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_state": f"cat {path}",
                    "command_on": f"echo '{oncmd}' > {path}",
                    "command_off": f"echo '{offcmd}' > {path}",
                    "value_template": '{{ value_json.status=="ok" }}',
                }
            },
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_ON

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF


async def test_state_code(opp: OpenPeerPower) -> None:
    """Test with state code."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "switch_status")
        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_state": f"cat {path}",
                    "command_on": f"echo 1 > {path}",
                    "command_off": f"echo 0 > {path}",
                }
            },
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_OFF

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_ON

        await opp.services.async_call(
            DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test"},
            blocking=True,
        )

        entity_state = opp.states.get("switch.test")
        assert entity_state
        assert entity_state.state == STATE_ON


async def test_assumed_state_should_be_true_if_command_state_is_none(
    opp: OpenPeerPower,
) -> None:
    """Test with state value."""

    await setup_test_entity(
        opp,
        {
            "test": {
                "command_on": "echo 'on command'",
                "command_off": "echo 'off command'",
            }
        },
    )
    entity_state = opp.states.get("switch.test")
    assert entity_state
    assert entity_state.attributes["assumed_state"]


async def test_assumed_state_should_absent_if_command_state_present(
    opp: OpenPeerPower,
) -> None:
    """Test with state value."""

    await setup_test_entity(
        opp,
        {
            "test": {
                "command_on": "echo 'on command'",
                "command_off": "echo 'off command'",
                "command_state": "cat {}",
            }
        },
    )
    entity_state = opp.states.get("switch.test")
    assert entity_state
    assert "assumed_state" not in entity_state.attributes


async def test_name_is_set_correctly(opp: OpenPeerPower) -> None:
    """Test that name is set correctly."""
    await setup_test_entity(
        opp,
        {
            "test": {
                "command_on": "echo 'on command'",
                "command_off": "echo 'off command'",
                "friendly_name": "Test friendly name!",
            }
        },
    )

    entity_state = opp.states.get("switch.test")
    assert entity_state.name == "Test friendly name!"


async def test_switch_command_state_fail(caplog: Any, opp: OpenPeerPower) -> None:
    """Test that switch failures are handled correctly."""
    await setup_test_entity(
        opp,
        {
            "test": {
                "command_on": "exit 0",
                "command_off": "exit 0'",
                "command_state": "echo 1",
            }
        },
    )

    async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL)
    await opp.async_block_till_done()

    entity_state = opp.states.get("switch.test")
    assert entity_state.state == "on"

    await opp.services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.test"},
        blocking=True,
    )
    await opp.async_block_till_done()

    entity_state = opp.states.get("switch.test")
    assert entity_state.state == "on"

    assert "Command failed" in caplog.text


async def test_switch_command_state_code_exceptions(
    caplog: Any, opp: OpenPeerPower
) -> None:
    """Test that switch state code exceptions are handled correctly."""

    with patch(
        "openpeerpower.components.command_line.subprocess.check_output",
        side_effect=[
            subprocess.TimeoutExpired("cmd", 10),
            subprocess.SubprocessError(),
        ],
    ) as check_output:
        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_on": "exit 0",
                    "command_off": "exit 0'",
                    "command_state": "echo 1",
                }
            },
        )
        async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL)
        await opp.async_block_till_done()
        assert check_output.called
        assert "Timeout for command" in caplog.text

        async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL * 2)
        await opp.async_block_till_done()
        assert check_output.called
        assert "Error trying to exec command" in caplog.text


async def test_switch_command_state_value_exceptions(
    caplog: Any, opp: OpenPeerPower
) -> None:
    """Test that switch state value exceptions are handled correctly."""

    with patch(
        "openpeerpower.components.command_line.subprocess.check_output",
        side_effect=[
            subprocess.TimeoutExpired("cmd", 10),
            subprocess.SubprocessError(),
        ],
    ) as check_output:
        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_on": "exit 0",
                    "command_off": "exit 0'",
                    "command_state": "echo 1",
                    "value_template": '{{ value=="1" }}',
                }
            },
        )
        async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL)
        await opp.async_block_till_done()
        assert check_output.call_count == 1
        assert "Timeout for command" in caplog.text

        async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL * 2)
        await opp.async_block_till_done()
        assert check_output.call_count == 2
        assert "Error trying to exec command" in caplog.text


async def test_no_switches(caplog: Any, opp: OpenPeerPower) -> None:
    """Test with no switches."""

    await setup_test_entity(opp, {})
    assert "No switches" in caplog.text
