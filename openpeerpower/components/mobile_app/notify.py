"""Support for mobile_app push notifications."""
import asyncio
import logging

import aiohttp
import async_timeout

from openpeerpower.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
    BaseNotificationService,
)
from openpeerpower.const import (
    HTTP_ACCEPTED,
    HTTP_CREATED,
    HTTP_OK,
    HTTP_TOO_MANY_REQUESTS,
)
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.util.dt as dt_util

from .const import (
    ATTR_APP_DATA,
    ATTR_APP_ID,
    ATTR_APP_VERSION,
    ATTR_DEVICE_NAME,
    ATTR_OS_VERSION,
    ATTR_PUSH_RATE_LIMITS,
    ATTR_PUSH_RATE_LIMITS_ERRORS,
    ATTR_PUSH_RATE_LIMITS_MAXIMUM,
    ATTR_PUSH_RATE_LIMITS_RESETS_AT,
    ATTR_PUSH_RATE_LIMITS_SUCCESSFUL,
    ATTR_PUSH_TOKEN,
    ATTR_PUSH_URL,
    DATA_CONFIG_ENTRIES,
    DATA_NOTIFY,
    DOMAIN,
)
from .util import supports_push

_LOGGER = logging.getLogger(__name__)


def push_registrations(opp):
    """Return a dictionary of push enabled registrations."""
    targets = {}

    for webhook_id, entry in opp.data[DOMAIN][DATA_CONFIG_ENTRIES].items():
        if not supports_push(opp, webhook_id):
            continue

        targets[entry.data[ATTR_DEVICE_NAME]] = webhook_id

    return targets


# pylint: disable=invalid-name
def log_rate_limits(opp, device_name, resp, level=logging.INFO):
    """Output rate limit log line at given level."""
    if ATTR_PUSH_RATE_LIMITS not in resp:
        return

    rate_limits = resp[ATTR_PUSH_RATE_LIMITS]
    resetsAt = rate_limits[ATTR_PUSH_RATE_LIMITS_RESETS_AT]
    resetsAtTime = dt_util.parse_datetime(resetsAt) - dt_util.utcnow()
    rate_limit_msg = (
        "mobile_app push notification rate limits for %s: "
        "%d sent, %d allowed, %d errors, "
        "resets in %s"
    )
    _LOGGER.log(
        level,
        rate_limit_msg,
        device_name,
        rate_limits[ATTR_PUSH_RATE_LIMITS_SUCCESSFUL],
        rate_limits[ATTR_PUSH_RATE_LIMITS_MAXIMUM],
        rate_limits[ATTR_PUSH_RATE_LIMITS_ERRORS],
        str(resetsAtTime).split(".")[0],
    )


async def async_get_service(opp, config, discovery_info=None):
    """Get the mobile_app notification service."""
    session = async_get_clientsession(opp)
    service = opp.data[DOMAIN][DATA_NOTIFY] = MobileAppNotificationService(session)
    return service


class MobileAppNotificationService(BaseNotificationService):
    """Implement the notification service for mobile_app."""

    def __init__(self, session):
        """Initialize the service."""
        self._session = session

    @property
    def targets(self):
        """Return a dictionary of registered targets."""
        return push_registrations(self.opp)

    async def async_send_message(self, message="", **kwargs):
        """Send a message to the Lambda APNS gateway."""
        data = {ATTR_MESSAGE: message}

        if kwargs.get(ATTR_TITLE) is not None:
            # Remove default title from notifications.
            if kwargs.get(ATTR_TITLE) != ATTR_TITLE_DEFAULT:
                data[ATTR_TITLE] = kwargs.get(ATTR_TITLE)

        targets = kwargs.get(ATTR_TARGET)

        if not targets:
            targets = push_registrations(self.opp).values()

        if kwargs.get(ATTR_DATA) is not None:
            data[ATTR_DATA] = kwargs.get(ATTR_DATA)

        for target in targets:
            entry = self.opp.data[DOMAIN][DATA_CONFIG_ENTRIES][target]
            entry_data = entry.data

            app_data = entry_data[ATTR_APP_DATA]
            push_token = app_data[ATTR_PUSH_TOKEN]
            push_url = app_data[ATTR_PUSH_URL]

            data[ATTR_PUSH_TOKEN] = push_token

            reg_info = {
                ATTR_APP_ID: entry_data[ATTR_APP_ID],
                ATTR_APP_VERSION: entry_data[ATTR_APP_VERSION],
            }
            if ATTR_OS_VERSION in entry_data:
                reg_info[ATTR_OS_VERSION] = entry_data[ATTR_OS_VERSION]

            data["registration_info"] = reg_info

            try:
                with async_timeout.timeout(10):
                    response = await self._session.post(push_url, json=data)
                    result = await response.json()

                if response.status in [HTTP_OK, HTTP_CREATED, HTTP_ACCEPTED]:
                    log_rate_limits(self.opp, entry_data[ATTR_DEVICE_NAME], result)
                    continue

                fallback_error = result.get("errorMessage", "Unknown error")
                fallback_message = (
                    f"Internal server error, please try again later: {fallback_error}"
                )
                message = result.get("message", fallback_message)

                if "message" in result:
                    if message[-1] not in [".", "?", "!"]:
                        message += "."
                    message += (
                        " This message is generated externally to Open Peer Power."
                    )

                if response.status == HTTP_TOO_MANY_REQUESTS:
                    _LOGGER.warning(message)
                    log_rate_limits(
                        self.opp, entry_data[ATTR_DEVICE_NAME], result, logging.WARNING
                    )
                else:
                    _LOGGER.error(message)

            except asyncio.TimeoutError:
                _LOGGER.error("Timeout sending notification to %s", push_url)
            except aiohttp.ClientError as err:
                _LOGGER.error("Error sending notification to %s: %r", push_url, err)
