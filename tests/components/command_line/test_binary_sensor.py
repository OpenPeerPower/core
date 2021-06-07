"""The tests for the Command line Binary sensor platform."""
from __future__ import annotations

from typing import Any

from openpeerpower import setup
from openpeerpower.components.binary_sensor import DOMAIN
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.core import OpenPeerPower


async def setup_test_entity(opp: OpenPeerPower, config_dict: dict[str, Any]) -> None:
    """Set up a test command line binary_sensor entity."""
    assert await setup.async_setup_component(
        opp,
        DOMAIN,
        {DOMAIN: {"platform": "command_line", "name": "Test", **config_dict}},
    )
    await opp.async_block_till_done()


async def test_setup(opp: OpenPeerPower) -> None:
    """Test sensor setup."""
    await setup_test_entity(
        opp,
        {
            "command": "echo 1",
            "payload_on": "1",
            "payload_off": "0",
        },
    )

    entity_state = opp.states.get("binary_sensor.test")
    assert entity_state
    assert entity_state.state == STATE_ON
    assert entity_state.name == "Test"


async def test_template(opp: OpenPeerPower) -> None:
    """Test setting the state with a template."""

    await setup_test_entity(
        opp,
        {
            "command": "echo 10",
            "payload_on": "1.0",
            "payload_off": "0",
            "value_template": "{{ value | multiply(0.1) }}",
        },
    )

    entity_state = opp.states.get("binary_sensor.test")
    assert entity_state.state == STATE_ON


async def test_sensor_off(opp: OpenPeerPower) -> None:
    """Test setting the state with a template."""
    await setup_test_entity(
        opp,
        {
            "command": "echo 0",
            "payload_on": "1",
            "payload_off": "0",
        },
    )
    entity_state = opp.states.get("binary_sensor.test")
    assert entity_state.state == STATE_OFF
