"""Clicksend platform for notify component."""
import json
import logging

from aiohttp.hdrs import CONTENT_TYPE
import requests
import voluptuous as vol

from openpeerpower.components.notify import PLATFORM_SCHEMA, BaseNotificationService
from openpeerpower.const import (
    CONF_API_KEY,
    CONF_RECIPIENT,
    CONF_SENDER,
    CONF_USERNAME,
    CONTENT_TYPE_JSON,
    HTTP_OK,
)
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

BASE_API_URL = "https://rest.clicksend.com/v3"
DEFAULT_SENDER = "opp"
TIMEOUT = 5

HEADERS = {CONTENT_TYPE: CONTENT_TYPE_JSON}


PLATFORM_SCHEMA = vol.Schema(
    vol.All(
        PLATFORM_SCHEMA.extend(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_RECIPIENT, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_SENDER, default=DEFAULT_SENDER): cv.string,
            }
        )
    )
)


def get_service(opp, config, discovery_info=None):
    """Get the ClickSend notification service."""
    if not _authenticate(config):
        _LOGGER.error("You are not authorized to access ClickSend")
        return None
    return ClicksendNotificationService(config)


class ClicksendNotificationService(BaseNotificationService):
    """Implementation of a notification service for the ClickSend service."""

    def __init__(self, config):
        """Initialize the service."""
        self.username = config[CONF_USERNAME]
        self.api_key = config[CONF_API_KEY]
        self.recipients = config[CONF_RECIPIENT]
        self.sender = config[CONF_SENDER]

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        data = {"messages": []}
        for recipient in self.recipients:
            data["messages"].append(
                {
                    "source": "opp:notify",
                    "from": self.sender,
                    "to": recipient,
                    "body": message,
                }
            )

        api_url = f"{BASE_API_URL}/sms/send"
        resp = requests.post(
            api_url,
            data=json.dumps(data),
            headers=HEADERS,
            auth=(self.username, self.api_key),
            timeout=TIMEOUT,
        )
        if resp.status_code == HTTP_OK:
            return

        obj = json.loads(resp.text)
        response_msg = obj.get("response_msg")
        response_code = obj.get("response_code")
        _LOGGER.error(
            "Error %s : %s (Code %s)", resp.status_code, response_msg, response_code
        )


def _authenticate(config):
    """Authenticate with ClickSend."""
    api_url = f"{BASE_API_URL}/account"
    resp = requests.get(
        api_url,
        headers=HEADERS,
        auth=(config[CONF_USERNAME], config[CONF_API_KEY]),
        timeout=TIMEOUT,
    )
    if resp.status_code != HTTP_OK:
        return False
    return True
