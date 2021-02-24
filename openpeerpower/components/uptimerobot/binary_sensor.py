"""A platform that to monitor Uptime Robot monitors."""
import logging

from pyuptimerobot import UptimeRobot
import voluptuous as vol

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from openpeerpower.const import ATTR_ATTRIBUTION, CONF_API_KEY
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_TARGET = "target"

ATTRIBUTION = "Data provided by Uptime Robot"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_API_KEY): cv.string})


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Uptime Robot binary_sensors."""

    up_robot = UptimeRobot()
    api_key = config.get(CONF_API_KEY)
    monitors = up_robot.getMonitors(api_key)

    devices = []
    if not monitors or monitors.get("stat") != "ok":
        _LOGGER.error("Error connecting to Uptime Robot")
        return

    for monitor in monitors["monitors"]:
        devices.append(
            UptimeRobotBinarySensor(
                api_key,
                up_robot,
                monitor["id"],
                monitor["friendly_name"],
                monitor["url"],
            )
        )

    add_entities(devices, True)


class UptimeRobotBinarySensor(BinarySensorEntity):
    """Representation of a Uptime Robot binary sensor."""

    def __init__(self, api_key, up_robot, monitor_id, name, target):
        """Initialize Uptime Robot the binary sensor."""
        self._api_key = api_key
        self._monitor_id = str(monitor_id)
        self._name = name
        self._target = target
        self._up_robot = up_robot
        self._state = None

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def device_state_attributes(self):
        """Return the state attributes of the binary sensor."""
        return {ATTR_ATTRIBUTION: ATTRIBUTION, ATTR_TARGET: self._target}

    def update(self):
        """Get the latest state of the binary sensor."""
        monitor = self._up_robot.getMonitors(self._api_key, self._monitor_id)
        if not monitor or monitor.get("stat") != "ok":
            _LOGGER.warning("Failed to get new state")
            return
        status = monitor["monitors"][0]["status"]
        self._state = 1 if status == 2 else 0
