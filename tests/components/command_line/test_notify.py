"""The tests for the command line notification platform."""
from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.components.notify import DOMAIN
from openpeerpower.core import OpenPeerPower


async def setup_test_service(opp: OpenPeerPower, config_dict: dict[str, Any]) -> None:
    """Set up a test command line notify service."""
    assert await setup.async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: [
                {"platform": "command_line", "name": "Test", **config_dict},
            ]
        },
    )
    await opp.async_block_till_done()


async def test_setup(opp: OpenPeerPower) -> None:
    """Test sensor setup."""
    await setup_test_service(opp, {"command": "exit 0"})
    assert opp.services.has_service(DOMAIN, "test")


async def test_bad_config(opp: OpenPeerPower) -> None:
    """Test set up the platform with bad/missing configuration."""
    await setup_test_service(opp, {})
    assert not opp.services.has_service(DOMAIN, "test")


async def test_command_line_output(opp: OpenPeerPower) -> None:
    """Test the command line output."""
    with tempfile.TemporaryDirectory() as tempdirname:
        filename = os.path.join(tempdirname, "message.txt")
        message = "one, two, testing, testing"
        await setup_test_service(
            opp,
            {
                "command": f"cat > {filename}",
            },
        )

        assert opp.services.has_service(DOMAIN, "test")

        assert await opp.services.async_call(
            DOMAIN, "test", {"message": message}, blocking=True
        )
        with open(filename) as handle:
            # the echo command adds a line break
            assert message == handle.read()


async def test_error_for_none_zero_exit_code(caplog: Any, opp: OpenPeerPower) -> None:
    """Test if an error is logged for non zero exit codes."""
    await setup_test_service(
        opp,
        {
            "command": "exit 1",
        },
    )

    assert await opp.services.async_call(
        DOMAIN, "test", {"message": "error"}, blocking=True
    )
    assert "Command failed" in caplog.text


async def test_timeout(caplog: Any, opp: OpenPeerPower) -> None:
    """Test blocking is not forever."""
    await setup_test_service(
        opp,
        {
            "command": "sleep 10000",
            "command_timeout": 0.0000001,
        },
    )
    assert await opp.services.async_call(
        DOMAIN, "test", {"message": "error"}, blocking=True
    )
    assert "Timeout" in caplog.text


async def test_subprocess_exceptions(caplog: Any, opp: OpenPeerPower) -> None:
    """Test that notify subprocess exceptions are handled correctly."""

    with patch(
        "openpeerpower.components.command_line.notify.subprocess.Popen"
    ) as check_output:
        check_output.return_value.__enter__ = check_output
        check_output.return_value.communicate.side_effect = [
            subprocess.TimeoutExpired("cmd", 10),
            None,
            subprocess.SubprocessError(),
        ]

        await setup_test_service(opp, {"command": "exit 0"})
        assert await opp.services.async_call(
            DOMAIN, "test", {"message": "error"}, blocking=True
        )
        assert check_output.call_count == 2
        assert "Timeout for command" in caplog.text

        assert await opp.services.async_call(
            DOMAIN, "test", {"message": "error"}, blocking=True
        )
        assert check_output.call_count == 4
        assert "Error trying to exec command" in caplog.text
