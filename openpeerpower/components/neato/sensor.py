"""Support for Neato sensors."""
from datetime import timedelta
import logging

from pybotvac.exceptions import NeatoRobotException

from openpeerpower.components.sensor import DEVICE_CLASS_BATTERY, SensorEntity
from openpeerpower.const import PERCENTAGE

from .const import NEATO_DOMAIN, NEATO_LOGIN, NEATO_ROBOTS, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=SCAN_INTERVAL_MINUTES)

BATTERY = "Battery"


async def async_setup_entry(opp, entry, async_add_entities):
    """Set up the Neato sensor using config entry."""
    dev = []
    neato = opp.data.get(NEATO_LOGIN)
    for robot in opp.data[NEATO_ROBOTS]:
        dev.append(NeatoSensor(neato, robot))

    if not dev:
        return

    _LOGGER.debug("Adding robots for sensors %s", dev)
    async_add_entities(dev, True)


class NeatoSensor(SensorEntity):
    """Neato sensor."""

    def __init__(self, neato, robot):
        """Initialize Neato sensor."""
        self.robot = robot
        self._available = False
        self._robot_name = f"{self.robot.name} {BATTERY}"
        self._robot_serial = self.robot.serial
        self._state = None

    def update(self):
        """Update Neato Sensor."""
        try:
            self._state = self.robot.state
        except NeatoRobotException as ex:
            if self._available:
                _LOGGER.error(
                    "Neato sensor connection error for '%s': %s", self.entity_id, ex
                )
            self._state = None
            self._available = False
            return

        self._available = True
        _LOGGER.debug("self._state=%s", self._state)

    @property
    def name(self):
        """Return the name of this sensor."""
        return self._robot_name

    @property
    def unique_id(self):
        """Return unique ID."""
        return self._robot_serial

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_BATTERY

    @property
    def available(self):
        """Return availability."""
        return self._available

    @property
    def state(self):
        """Return the state."""
        return self._state["details"]["charge"] if self._state else None

    @property
    def unit_of_measurement(self):
        """Return unit of measurement."""
        return PERCENTAGE

    @property
    def device_info(self):
        """Device info for neato robot."""
        return {"identifiers": {(NEATO_DOMAIN, self._robot_serial)}}
