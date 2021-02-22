"""Support for Dovado router."""
from datetime import timedelta
import logging

import dovado
import voluptuous as vol

from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEVICE_DEFAULT_NAME,
)
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = "dovado"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT): cv.port,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)


def setup(opp, config):
    """Set up the Dovado component."""

    opp.data[DOMAIN] = DovadoData(
        dovado.Dovado(
            config[DOMAIN][CONF_USERNAME],
            config[DOMAIN][CONF_PASSWORD],
            config[DOMAIN].get(CONF_HOST),
            config[DOMAIN].get(CONF_PORT),
        )
    )
    return True


class DovadoData:
    """Maintain a connection to the router."""

    def __init__(self, client):
        """Set up a new Dovado connection."""
        self._client = client
        self.state = {}

    @property
    def name(self):
        """Name of the router."""
        return self.state.get("product name", DEVICE_DEFAULT_NAME)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update device state."""
        try:
            self.state = self._client.state or {}
            if not self.state:
                return False
            self.state.update(connected=self.state.get("modem status") == "CONNECTED")
            _LOGGER.debug("Received: %s", self.state)
            return True
        except OSError as error:
            _LOGGER.warning("Could not contact the router: %s", error)

    @property
    def client(self):
        """Dovado client instance."""
        return self._client
