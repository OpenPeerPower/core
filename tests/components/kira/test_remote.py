"""The tests for Kira sensor platform."""
import unittest
from unittest.mock import MagicMock

from openpeerpower.components.kira import remote as kira

from tests.common import get_test_open_peer_power

SERVICE_SEND_COMMAND = "send_command"

TEST_CONFIG = {kira.DOMAIN: {"devices": [{"host": "127.0.0.1", "port": 17324}]}}

DISCOVERY_INFO = {"name": "kira", "device": "kira"}


class TestKiraSensor(unittest.TestCase):
    """Tests the Kira Sensor platform."""

    # pylint: disable=invalid-name
    DEVICES = []

    def add_entities(self, devices):
        """Mock add devices."""
        for device in devices:
            self.DEVICES.append(device)

    def setUp(self):
        """Initialize values for this testcase class."""
        self.opp = get_test_open_peer_power()
        self.mock_kira = MagicMock()
        self.opp.data[kira.DOMAIN] = {kira.CONF_REMOTE: {}}
        self.opp.data[kira.DOMAIN][kira.CONF_REMOTE]["kira"] = self.mock_kira
        self.addCleanup(self.opp.stop)

    def test_service_call(self):
        """Test Kira's ability to send commands."""
        kira.setup_platform(self.opp, TEST_CONFIG, self.add_entities, DISCOVERY_INFO)
        assert len(self.DEVICES) == 1
        remote = self.DEVICES[0]

        assert remote.name == "kira"

        command = ["FAKE_COMMAND"]
        device = "FAKE_DEVICE"
        commandTuple = (command[0], device)
        remote.send_command(device=device, command=command)

        self.mock_kira.sendCode.assert_called_with(commandTuple)
