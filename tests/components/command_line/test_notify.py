"""The tests for the command line notification platform."""
import os
import subprocess
import tempfile
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.components.notify import DOMAIN
from openpeerpower.helpers.typing import Any, Dict, OpenPeerPowerType


async def setup_test_service(
    opp: OpenPeerPowerType, config_dict: Dict[str, Any]
) -> None:
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


async def test_setup(opp: OpenPeerPowerType) -> None:
    """Test sensor setup."""
    await setup_test_service(opp, {"command": "exit 0"})
    assert opp.services.has_service(DOMAIN, "test")


async def test_bad_config(opp: OpenPeerPowerType) -> None:
    """Test set up the platform with bad/missing configuration."""
    await setup_test_service(opp, {})
    assert not opp.services.has_service(DOMAIN, "test")


async def test_command_line_output(opp: OpenPeerPowerType) -> None:
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


async def test_error_for_none_zero_exit_code(
    caplog: Any, opp: OpenPeerPowerType
) -> None:
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


async def test_timeout(caplog: Any, opp: OpenPeerPowerType) -> None:
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


async def test_subprocess_exceptions(caplog: Any, opp: OpenPeerPowerType) -> None:
    """Test that notify subprocess exceptions are handled correctly."""

    with patch(
        "openpeerpower.components.command_line.notify.subprocess.Popen",
        side_effect=[
            subprocess.TimeoutExpired("cmd", 10),
            subprocess.SubprocessError(),
        ],
    ) as check_output:
        await setup_test_service(opp, {"command": "exit 0"})
        assert await opp.services.async_call(
            DOMAIN, "test", {"message": "error"}, blocking=True
        )
        assert check_output.call_count == 1
        assert "Timeout for command" in caplog.text

        assert await opp.services.async_call(
            DOMAIN, "test", {"message": "error"}, blocking=True
        )
        assert check_output.call_count == 2
        assert "Error trying to exec command" in caplog.text
