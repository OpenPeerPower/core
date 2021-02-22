"""The tests for the command line notification platform."""
import os
import tempfile
import unittest
from unittest.mock import patch

import openpeerpower.components.notify as notify
from openpeerpower.setup import async_setup_component, setup_component

from tests.common import assert_setup_component, get_test_open_peer_power


class TestCommandLine(unittest.TestCase):
    """Test the command line notifications."""

    def setUp(self):  # pylint: disable=invalid-name
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()
        self.addCleanup(self.tear_down_cleanup)

    def tear_down_cleanup(self):
        """Stop down everything that was started."""
        self.opp.stop()

    def test_setup(self):
        """Test setup."""
        with assert_setup_component(1) as handle_config:
            assert setup_component(
                self.opp,
                "notify",
                {
                    "notify": {
                        "name": "test",
                        "platform": "command_line",
                        "command": "echo $(cat); exit 1",
                    }
                },
            )
        assert handle_config[notify.DOMAIN]

    def test_bad_config(self):
        """Test set up the platform with bad/missing configuration."""
        config = {notify.DOMAIN: {"name": "test", "platform": "command_line"}}
        with assert_setup_component(0) as handle_config:
            assert setup_component(self.opp, notify.DOMAIN, config)
        assert not handle_config[notify.DOMAIN]

    def test_command_line_output(self):
        """Test the command line output."""
        with tempfile.TemporaryDirectory() as tempdirname:
            filename = os.path.join(tempdirname, "message.txt")
            message = "one, two, testing, testing"
            with assert_setup_component(1) as handle_config:
                assert setup_component(
                    self.opp,
                    notify.DOMAIN,
                    {
                        "notify": {
                            "name": "test",
                            "platform": "command_line",
                            "command": f"echo $(cat) > {filename}",
                        }
                    },
                )
            assert handle_config[notify.DOMAIN]

            assert self.opp.services.call(
                "notify", "test", {"message": message}, blocking=True
            )

            with open(filename) as fil:
                # the echo command adds a line break
                assert fil.read() == f"{message}\n"

    @patch("openpeerpower.components.command_line.notify._LOGGER.error")
    def test_error_for_none_zero_exit_code(self, mock_error):
        """Test if an error is logged for non zero exit codes."""
        with assert_setup_component(1) as handle_config:
            assert setup_component(
                self.opp,
                notify.DOMAIN,
                {
                    "notify": {
                        "name": "test",
                        "platform": "command_line",
                        "command": "echo $(cat); exit 1",
                    }
                },
            )
        assert handle_config[notify.DOMAIN]

        assert self.opp.services.call(
            "notify", "test", {"message": "error"}, blocking=True
        )
        assert mock_error.call_count == 1


async def test_timeout.opp, caplog):
    """Test we do not block forever."""
    assert await async_setup_component(
        opp.
        notify.DOMAIN,
        {
            "notify": {
                "name": "test",
                "platform": "command_line",
                "command": "sleep 10000",
                "command_timeout": 0.0000001,
            }
        },
    )
    await opp.async_block_till_done()
    assert await opp.services.async_call(
        "notify", "test", {"message": "error"}, blocking=True
    )
    await opp.async_block_till_done()
    assert "Timeout" in caplog.text
