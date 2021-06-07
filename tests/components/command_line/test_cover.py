"""The tests the cover command line platform."""
from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest.mock import patch

from openpeerpower import config as opp_config, setup
from openpeerpower.components.cover import DOMAIN, SCAN_INTERVAL
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_RELOAD,
    SERVICE_STOP_COVER,
)
from openpeerpower.core import OpenPeerPower
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed


async def setup_test_entity(opp: OpenPeerPower, config_dict: dict[str, Any]) -> None:
    """Set up a test command line notify service."""
    assert await setup.async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {"platform": "command_line", "covers": config_dict},
            ]
        },
    )
    await opp.async_block_till_done()


async def test_no_covers(caplog: Any, opp: OpenPeerPower) -> None:
    """Test that the cover does not polls when there's no state command."""

    with patch(
        "openpeerpower.components.command_line.subprocess.check_output",
        return_value=b"50\n",
    ):
        await setup_test_entity(opp, {})
        assert "No covers added" in caplog.text


async def test_no_poll_when_cover_has_no_command_state(opp: OpenPeerPower) -> None:
    """Test that the cover does not polls when there's no state command."""

    with patch(
        "openpeerpower.components.command_line.subprocess.check_output",
        return_value=b"50\n",
    ) as check_output:
        await setup_test_entity(opp, {"test": {}})
        async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL)
        await opp.async_block_till_done()
        assert not check_output.called


async def test_poll_when_cover_has_command_state(opp: OpenPeerPower) -> None:
    """Test that the cover polls when there's a state  command."""

    with patch(
        "openpeerpower.components.command_line.subprocess.check_output",
        return_value=b"50\n",
    ) as check_output:
        await setup_test_entity(opp, {"test": {"command_state": "echo state"}})
        async_fire_time_changed(opp, dt_util.utcnow() + SCAN_INTERVAL)
        await opp.async_block_till_done()
        check_output.assert_called_once_with(
            "echo state", shell=True, timeout=15  # nosec # shell by design
        )


async def test_state_value(opp: OpenPeerPower) -> None:
    """Test with state value."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "cover_status")
        await setup_test_entity(
            opp,
            {
                "test": {
                    "command_state": f"cat {path}",
                    "command_open": f"echo 1 > {path}",
                    "command_close": f"echo 1 > {path}",
                    "command_stop": f"echo 0 > {path}",
                    "value_template": "{{ value }}",
                }
            },
        )

        entity_state = opp.states.get("cover.test")
        assert entity_state
        assert entity_state.state == "unknown"

        await opp.services.async_call(
            DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
        )
        entity_state = opp.states.get("cover.test")
        assert entity_state
        assert entity_state.state == "open"

        await opp.services.async_call(
            DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
        )
        entity_state = opp.states.get("cover.test")
        assert entity_state
        assert entity_state.state == "open"

        await opp.services.async_call(
            DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
        )
        entity_state = opp.states.get("cover.test")
        assert entity_state
        assert entity_state.state == "closed"


async def test_reload(opp: OpenPeerPower) -> None:
    """Verify we can reload command_line covers."""

    await setup_test_entity(
        opp,
        {
            "test": {
                "command_state": "echo open",
                "value_template": "{{ value }}",
            }
        },
    )
    entity_state = opp.states.get("cover.test")
    assert entity_state
    assert entity_state.state == "unknown"

    yaml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "fixtures",
        "command_line/configuration.yaml",
    )
    with patch.object(opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            "command_line",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 1

    assert not opp.states.get("cover.test")
    assert opp.states.get("cover.from_yaml")


async def test_move_cover_failure(caplog: Any, opp: OpenPeerPower) -> None:
    """Test with state value."""

    await setup_test_entity(
        opp,
        {"test": {"command_open": "exit 1"}},
    )
    await opp.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
    )
    assert "Command failed" in caplog.text
