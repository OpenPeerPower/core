"""The tests for the Command line Binary sensor platform."""
import unittest

from openpeerpower.components.command_line import binary_sensor as command_line
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpowerr.helpers import template

from tests.common import get_test_home_assistant


class TestCommandSensorBinarySensor(unittest.TestCase):
    """Test the Command line Binary sensor."""

    def setUp(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()
        self.addCleanup(self.opp.stop)

    def test_setup(self):
        """Test sensor setup."""
        config = {
            "name": "Test",
            "command": "echo 1",
            "payload_on": "1",
            "payload_off": "0",
            "command_timeout": 15,
        }

        devices = []

        def add_dev_callback(devs, update):
            """Add callback to add devices."""
            for dev in devs:
                devices.append(dev)

        command_line.setup_platform(self.opp, config, add_dev_callback)

        assert 1 == len(devices)
        entity = devices[0]
        entity.update()
        assert "Test" == entity.name
        assert STATE_ON == entity.state

    def test_template(self):
        """Test setting the state with a template."""
        data = command_line.CommandSensorData(self.opp, "echo 10", 15)

        entity = command_line.CommandBinarySensor(
            self.opp,
            data,
            "test",
            None,
            "1.0",
            "0",
            template.Template("{{ value | multiply(0.1) }}", self.opp),
        )
        entity.update()
        assert STATE_ON == entity.state

    def test_sensor_off(self):
        """Test setting the state with a template."""
        data = command_line.CommandSensorData(self.opp, "echo 0", 15)

        entity = command_line.CommandBinarySensor(
            self.opp, data, "test", None, "1", "0", None
        )
        entity.update()
        assert STATE_OFF == entity.state
