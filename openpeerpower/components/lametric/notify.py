"""Support for LaMetric notifications."""
import logging

from lmnotify import Model, SimpleFrame, Sound
from oauthlib.oauth2 import TokenExpiredError
from requests.exceptions import ConnectionError as RequestsConnectionError
import voluptuous as vol

from openpeerpower.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from openpeerpower.const import CONF_ICON
import openpeerpower.helpers.config_validation as cv

from . import DOMAIN as LAMETRIC_DOMAIN

_LOGGER = logging.getLogger(__name__)

AVAILABLE_PRIORITIES = ["info", "warning", "critical"]
AVAILABLE_ICON_TYPES = ["none", "info", "alert"]

CONF_CYCLES = "cycles"
CONF_LIFETIME = "lifetime"
CONF_PRIORITY = "priority"
CONF_ICON_TYPE = "icon_type"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_ICON, default="a7956"): cv.string,
        vol.Optional(CONF_LIFETIME, default=10): cv.positive_int,
        vol.Optional(CONF_CYCLES, default=1): cv.positive_int,
        vol.Optional(CONF_PRIORITY, default="warning"): vol.In(AVAILABLE_PRIORITIES),
        vol.Optional(CONF_ICON_TYPE, default="info"): vol.In(AVAILABLE_ICON_TYPES),
    }
)


def get_service(opp, config, discovery_info=None):
    """Get the LaMetric notification service."""
    hlmn = opp.data.get(LAMETRIC_DOMAIN)
    return LaMetricNotificationService(
        hlmn,
        config[CONF_ICON],
        config[CONF_LIFETIME] * 1000,
        config[CONF_CYCLES],
        config[CONF_PRIORITY],
        config[CONF_ICON_TYPE],
    )


class LaMetricNotificationService(BaseNotificationService):
    """Implement the notification service for LaMetric."""

    def __init__(
        self, opplametricmanager, icon, lifetime, cycles, priority, icon_type
    ):
        """Initialize the service."""
        self.opplametricmanager = opplametricmanager
        self._icon = icon
        self._lifetime = lifetime
        self._cycles = cycles
        self._priority = priority
        self._icon_type = icon_type
        self._devices = []

    def send_message(self, message="", **kwargs):
        """Send a message to some LaMetric device."""

        targets = kwargs.get(ATTR_TARGET)
        data = kwargs.get(ATTR_DATA)
        _LOGGER.debug("Targets/Data: %s/%s", targets, data)
        icon = self._icon
        cycles = self._cycles
        sound = None
        priority = self._priority
        icon_type = self._icon_type

        # Additional data?
        if data is not None:
            if "icon" in data:
                icon = data["icon"]
            if "sound" in data:
                try:
                    sound = Sound(category="notifications", sound_id=data["sound"])
                    _LOGGER.debug("Adding notification sound %s", data["sound"])
                except AssertionError:
                    _LOGGER.error("Sound ID %s unknown, ignoring", data["sound"])
            if "cycles" in data:
                cycles = int(data["cycles"])
            if "icon_type" in data:
                if data["icon_type"] in AVAILABLE_ICON_TYPES:
                    icon_type = data["icon_type"]
                else:
                    _LOGGER.warning(
                        "Priority %s invalid, using default %s",
                        data["priority"],
                        priority,
                    )
            if "priority" in data:
                if data["priority"] in AVAILABLE_PRIORITIES:
                    priority = data["priority"]
                else:
                    _LOGGER.warning(
                        "Priority %s invalid, using default %s",
                        data["priority"],
                        priority,
                    )
        text_frame = SimpleFrame(icon, message)
        _LOGGER.debug(
            "Icon/Message/Cycles/Lifetime: %s, %s, %d, %d",
            icon,
            message,
            self._cycles,
            self._lifetime,
        )

        frames = [text_frame]

        model = Model(frames=frames, cycles=cycles, sound=sound)
        lmn = self.opplametricmanager.manager
        try:
            self._devices = lmn.get_devices()
        except TokenExpiredError:
            _LOGGER.debug("Token expired, fetching new token")
            lmn.get_token()
            self._devices = lmn.get_devices()
        except RequestsConnectionError:
            _LOGGER.warning(
                "Problem connecting to LaMetric, using cached devices instead"
            )
        for dev in self._devices:
            if targets is None or dev["name"] in targets:
                try:
                    lmn.set_device(dev)
                    lmn.send_notification(
                        model,
                        lifetime=self._lifetime,
                        priority=priority,
                        icon_type=icon_type,
                    )
                    _LOGGER.debug("Sent notification to LaMetric %s", dev["name"])
                except OSError:
                    _LOGGER.warning("Cannot connect to LaMetric %s", dev["name"])
