"""Prowl notification service."""
import asyncio
import logging

import async_timeout
import voluptuous as vol

from openpeerpower.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from openpeerpower.const import CONF_API_KEY, HTTP_OK
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
_RESOURCE = "https://api.prowlapp.com/publicapi/"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_API_KEY): cv.string})


async def async_get_service(opp, config, discovery_info=None):
    """Get the Prowl notification service."""
    return ProwlNotificationService(opp, config[CONF_API_KEY])


class ProwlNotificationService(BaseNotificationService):
    """Implement the notification service for Prowl."""

    def __init__(self, opp, api_key):
        """Initialize the service."""
        self._opp = opp
        self._api_key = api_key

    async def async_send_message(self, message, **kwargs):
        """Send the message to the user."""
        response = None
        session = None
        url = f"{_RESOURCE}add"
        data = kwargs.get(ATTR_DATA)
        payload = {
            "apikey": self._api_key,
            "application": "Open-Peer-Power",
            "event": kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT),
            "description": message,
            "priority": data["priority"] if data and "priority" in data else 0,
        }

        _LOGGER.debug("Attempting call Prowl service at %s", url)
        session = async_get_clientsession(self._opp)

        try:
            with async_timeout.timeout(10):
                response = await session.post(url, data=payload)
                result = await response.text()

            if response.status != HTTP_OK or "error" in result:
                _LOGGER.error(
                    "Prowl service returned http status %d, response %s",
                    response.status,
                    result,
                )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout accessing Prowl at %s", url)
