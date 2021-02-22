"""The tests for Kira sensor platform."""
import unittest
from unittest.mock import MagicMock

from openpeerpower.components.kira import sensor as kira

from tests.common import get_test_open_peer_power

TEST_CONFIG = {kira.DOMAIN: {"sensors": [{"host": "127.0.0.1", "port": 17324}]}}

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
        self opp =get_test_open_peer_power()
        mock_kira = MagicMock()
        self.opp.data[kira.DOMAIN] = {kira.CONF_SENSOR: {}}
        self.opp.data[kira.DOMAIN][kira.CONF_SENSOR]["kira"] = mock_kira
        self.addCleanup(self.opp.stop)

    # pylint: disable=protected-access
    def test_kira_sensor_callback(self):
        """Ensure Kira sensor properly updates its attributes from callback."""
        kira.setup_platform(self.opp, TEST_CONFIG, self.add_entities, DISCOVERY_INFO)
        assert len(self.DEVICES) == 1
        sensor = self.DEVICES[0]

        assert sensor.name == "kira"

        sensor opp =self.opp

        codeName = "FAKE_CODE"
        deviceName = "FAKE_DEVICE"
        codeTuple = (codeName, deviceName)
        sensor._update_callback(codeTuple)

        assert sensor.state == codeName
        assert sensor.device_state_attributes == {kira.CONF_DEVICE: deviceName}
