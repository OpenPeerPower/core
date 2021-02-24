"""Support for Ecobee Send Message service."""
import voluptuous as vol

from openpeerpower.components.notify import PLATFORM_SCHEMA, BaseNotificationService
import openpeerpower.helpers.config_validation as cv

from .const import CONF_INDEX, DOMAIN

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional(CONF_INDEX, default=0): cv.positive_int}
)


def get_service(opp, config, discovery_info=None):
    """Get the Ecobee notification service."""
    data = opp.data[DOMAIN]
    index = config.get(CONF_INDEX)
    return EcobeeNotificationService(data, index)


class EcobeeNotificationService(BaseNotificationService):
    """Implement the notification service for the Ecobee thermostat."""

    def __init__(self, data, thermostat_index):
        """Initialize the service."""
        self.data = data
        self.thermostat_index = thermostat_index

    def send_message(self, message="", **kwargs):
        """Send a message."""
        self.data.ecobee.send_message(self.thermostat_index, message)
