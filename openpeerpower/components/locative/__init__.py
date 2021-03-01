"""Support for Locative."""
import logging
from typing import Dict

from aiohttp import web
import voluptuous as vol

from openpeerpower.components.device_tracker import DOMAIN as DEVICE_TRACKER
from openpeerpower.const import (
    ATTR_ID,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_WEBHOOK_ID,
    HTTP_OK,
    HTTP_UNPROCESSABLE_ENTITY,
    STATE_NOT_HOME,
)
from openpeerpower.helpers import config_entry_flow
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

DOMAIN = "locative"
TRACKER_UPDATE = f"{DOMAIN}_tracker_update"


ATTR_DEVICE_ID = "device"
ATTR_TRIGGER = "trigger"


def _id(value: str) -> str:
    """Coerce id by removing '-'."""
    return value.replace("-", "")


def _validate_test_mode(obj: Dict) -> Dict:
    """Validate that id is provided outside of test mode."""
    if ATTR_ID not in obj and obj[ATTR_TRIGGER] != "test":
        raise vol.Invalid("Location id not specified")
    return obj


WEBHOOK_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(ATTR_LATITUDE): cv.latitude,
            vol.Required(ATTR_LONGITUDE): cv.longitude,
            vol.Required(ATTR_DEVICE_ID): cv.string,
            vol.Required(ATTR_TRIGGER): cv.string,
            vol.Optional(ATTR_ID): vol.All(cv.string, _id),
        },
        extra=vol.ALLOW_EXTRA,
    ),
    _validate_test_mode,
)


async def async_setup(opp, opp_config):
    """Set up the Locative component."""
    opp.data[DOMAIN] = {"devices": set(), "unsub_device_tracker": {}}
    return True


async def handle_webhook(opp, webhook_id, request):
    """Handle incoming webhook from Locative."""
    try:
        data = WEBHOOK_SCHEMA(dict(await request.post()))
    except vol.MultipleInvalid as error:
        return web.Response(text=error.error_message, status=HTTP_UNPROCESSABLE_ENTITY)

    device = data[ATTR_DEVICE_ID]
    location_name = data.get(ATTR_ID, data[ATTR_TRIGGER]).lower()
    direction = data[ATTR_TRIGGER]
    gps_location = (data[ATTR_LATITUDE], data[ATTR_LONGITUDE])

    if direction == "enter":
        async_dispatcher_send(opp, TRACKER_UPDATE, device, gps_location, location_name)
        return web.Response(text=f"Setting location to {location_name}", status=HTTP_OK)

    if direction == "exit":
        current_state = opp.states.get(f"{DEVICE_TRACKER}.{device}")

        if current_state is None or current_state.state == location_name:
            location_name = STATE_NOT_HOME
            async_dispatcher_send(
                opp, TRACKER_UPDATE, device, gps_location, location_name
            )
            return web.Response(text="Setting location to not home", status=HTTP_OK)

        # Ignore the message if it is telling us to exit a zone that we
        # aren't currently in. This occurs when a zone is entered
        # before the previous zone was exited. The enter message will
        # be sent first, then the exit message will be sent second.
        return web.Response(
            text=f"Ignoring exit from {location_name} (already in {current_state})",
            status=HTTP_OK,
        )

    if direction == "test":
        # In the app, a test message can be sent. Just return something to
        # the user to let them know that it works.
        return web.Response(text="Received test message.", status=HTTP_OK)

    _LOGGER.error("Received unidentified message from Locative: %s", direction)
    return web.Response(
        text=f"Received unidentified message: {direction}",
        status=HTTP_UNPROCESSABLE_ENTITY,
    )


async def async_setup_entry(opp, entry):
    """Configure based on config entry."""
    opp.components.webhook.async_register(
        DOMAIN, "Locative", entry.data[CONF_WEBHOOK_ID], handle_webhook
    )

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, DEVICE_TRACKER)
    )
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    opp.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    opp.data[DOMAIN]["unsub_device_tracker"].pop(entry.entry_id)()
    return await opp.config_entries.async_forward_entry_unload(entry, DEVICE_TRACKER)


async_remove_entry = config_entry_flow.webhook_async_remove_entry
