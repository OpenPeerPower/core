"""Support for customised Kankun SP3 Wifi switch."""
import logging

import requests
import voluptuous as vol

from openpeerpower.components.switch import PLATFORM_SCHEMA, SwitchEntity
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PATH,
    CONF_PORT,
    CONF_SWITCHES,
    CONF_USERNAME,
)
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 80
DEFAULT_PATH = "/cgi-bin/json.cgi"

SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_PATH, default=DEFAULT_PATH): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_SWITCHES): cv.schema_with_slug_keys(SWITCH_SCHEMA)}
)


def setup_platform.opp, config, add_entities_callback, discovery_info=None):
    """Set up Kankun Wifi switches."""
    switches = config.get("switches", {})
    devices = []

    for dev_name, properties in switches.items():
        devices.append(
            KankunSwitch(
               .opp,
                properties.get(CONF_NAME, dev_name),
                properties.get(CONF_HOST),
                properties.get(CONF_PORT, DEFAULT_PORT),
                properties.get(CONF_PATH, DEFAULT_PATH),
                properties.get(CONF_USERNAME),
                properties.get(CONF_PASSWORD),
            )
        )

    add_entities_callback(devices)


class KankunSwitch(SwitchEntity):
    """Representation of a Kankun Wifi switch."""

    def __init__(self,.opp, name, host, port, path, user, passwd):
        """Initialize the device."""
        self._opp =.opp
        self._name = name
        self._state = False
        self._url = f"http://{host}:{port}{path}"
        if user is not None:
            self._auth = (user, passwd)
        else:
            self._auth = None

    def _switch(self, newstate):
        """Switch on or off."""
        _LOGGER.info("Switching to state: %s", newstate)

        try:
            req = requests.get(
                f"{self._url}?set={newstate}", auth=self._auth, timeout=5
            )
            return req.json()["ok"]
        except requests.RequestException:
            _LOGGER.error("Switching failed")

    def _query_state(self):
        """Query switch state."""
        _LOGGER.info("Querying state from: %s", self._url)

        try:
            req = requests.get(f"{self._url}?get=state", auth=self._auth, timeout=5)
            return req.json()["state"] == "on"
        except requests.RequestException:
            _LOGGER.error("State query failed")

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def update(self):
        """Update device state."""
        self._state = self._query_state()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._switch("on"):
            self._state = True

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._switch("off"):
            self._state = False
