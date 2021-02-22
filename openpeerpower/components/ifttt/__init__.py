"""Support to trigger Maker IFTTT recipes."""
import json
import logging

import pyfttt
import requests
import voluptuous as vol

from openpeerpower.const import CONF_WEBHOOK_ID, HTTP_OK
from openpeerpower.helpers import config_entry_flow
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

EVENT_RECEIVED = "ifttt_webhook_received"

ATTR_EVENT = "event"
ATTR_TARGET = "target"
ATTR_VALUE1 = "value1"
ATTR_VALUE2 = "value2"
ATTR_VALUE3 = "value3"

CONF_KEY = "key"

SERVICE_PUSH_ALARM_STATE = "push_alarm_state"
SERVICE_TRIGGER = "trigger"

SERVICE_TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EVENT): cv.string,
        vol.Optional(ATTR_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_VALUE1): cv.string,
        vol.Optional(ATTR_VALUE2): cv.string,
        vol.Optional(ATTR_VALUE3): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {vol.Required(CONF_KEY): vol.Any({cv.string: cv.string}, cv.string)}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_opp, config):
    """Set up the IFTTT service component."""
    if DOMAIN not in config:
        return True

    api_keys = config[DOMAIN][CONF_KEY]
    if isinstance(api_keys, str):
        api_keys = {"default": api_keys}

    def trigger_service(call):
        """Handle IFTTT trigger service calls."""
        event = call.data[ATTR_EVENT]
        targets = call.data.get(ATTR_TARGET, list(api_keys))
        value1 = call.data.get(ATTR_VALUE1)
        value2 = call.data.get(ATTR_VALUE2)
        value3 = call.data.get(ATTR_VALUE3)

        target_keys = {}
        for target in targets:
            if target not in api_keys:
                _LOGGER.error("No IFTTT api key for %s", target)
                continue
            target_keys[target] = api_keys[target]

        try:

            for target, key in target_keys.items():
                res = pyfttt.send_event(key, event, value1, value2, value3)
                if res.status_code != HTTP_OK:
                    _LOGGER.error("IFTTT reported error sending event to %s", target)
        except requests.exceptions.RequestException:
            _LOGGER.exception("Error communicating with IFTTT")

   .opp.services.async_register(
        DOMAIN, SERVICE_TRIGGER, trigger_service, schema=SERVICE_TRIGGER_SCHEMA
    )

    return True


async def handle_webhook.opp, webhook_id, request):
    """Handle webhook callback."""
    body = await request.text()
    try:
        data = json.loads(body) if body else {}
    except ValueError:
        _LOGGER.error(
            "Received invalid data from IFTTT. Data needs to be formatted as JSON: %s",
            body,
        )
        return

    if not isinstance(data, dict):
        _LOGGER.error(
            "Received invalid data from IFTTT. Data needs to be a dictionary: %s", data
        )
        return

    data["webhook_id"] = webhook_id
   .opp.bus.async_fire(EVENT_RECEIVED, data)


async def async_setup_entry.opp, entry):
    """Configure based on config entry."""
   .opp.components.webhook.async_register(
        DOMAIN, "IFTTT", entry.data[CONF_WEBHOOK_ID], handle_webhook
    )
    return True


async def async_unload_entry.opp, entry):
    """Unload a config entry."""
   .opp.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    return True


async_remove_entry = config_entry_flow.webhook_async_remove_entry
