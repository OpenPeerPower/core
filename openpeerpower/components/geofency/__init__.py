"""Support for Geofency."""
from aiohttp import web
import voluptuous as vol

from openpeerpower.components.device_tracker import DOMAIN as DEVICE_TRACKER
from openpeerpower.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_NAME,
    CONF_WEBHOOK_ID,
    HTTP_OK,
    HTTP_UNPROCESSABLE_ENTITY,
    STATE_NOT_HOME,
)
from openpeerpower.helpers import config_entry_flow
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.util import slugify

from .const import DOMAIN

CONF_MOBILE_BEACONS = "mobile_beacons"

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Optional(CONF_MOBILE_BEACONS, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

ATTR_ADDRESS = "address"
ATTR_BEACON_ID = "beaconUUID"
ATTR_CURRENT_LATITUDE = "currentLatitude"
ATTR_CURRENT_LONGITUDE = "currentLongitude"
ATTR_DEVICE = "device"
ATTR_ENTRY = "entry"

BEACON_DEV_PREFIX = "beacon"

LOCATION_ENTRY = "1"
LOCATION_EXIT = "0"

TRACKER_UPDATE = f"{DOMAIN}_tracker_update"


def _address(value: str) -> str:
    r"""Coerce address by replacing '\n' with ' '."""
    return value.replace("\n", " ")


WEBHOOK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ADDRESS): vol.All(cv.string, _address),
        vol.Required(ATTR_DEVICE): vol.All(cv.string, slugify),
        vol.Required(ATTR_ENTRY): vol.Any(LOCATION_ENTRY, LOCATION_EXIT),
        vol.Required(ATTR_LATITUDE): cv.latitude,
        vol.Required(ATTR_LONGITUDE): cv.longitude,
        vol.Required(ATTR_NAME): vol.All(cv.string, slugify),
        vol.Optional(ATTR_CURRENT_LATITUDE): cv.latitude,
        vol.Optional(ATTR_CURRENT_LONGITUDE): cv.longitude,
        vol.Optional(ATTR_BEACON_ID): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, opp_config):
    """Set up the Geofency component."""
    config = opp_config.get(DOMAIN, {})
    mobile_beacons = config.get(CONF_MOBILE_BEACONS, [])
    opp.data[DOMAIN] = {
        "beacons": [slugify(beacon) for beacon in mobile_beacons],
        "devices": set(),
        "unsub_device_tracker": {},
    }
    return True


async def handle_webhook(opp, webhook_id, request):
    """Handle incoming webhook from Geofency."""
    try:
        data = WEBHOOK_SCHEMA(dict(await request.post()))
    except vol.MultipleInvalid as error:
        return web.Response(text=error.error_message, status=HTTP_UNPROCESSABLE_ENTITY)

    if _is_mobile_beacon(data, opp.data[DOMAIN]["beacons"]):
        return _set_location(opp, data, None)
    if data["entry"] == LOCATION_ENTRY:
        location_name = data["name"]
    else:
        location_name = STATE_NOT_HOME
        if ATTR_CURRENT_LATITUDE in data:
            data[ATTR_LATITUDE] = data[ATTR_CURRENT_LATITUDE]
            data[ATTR_LONGITUDE] = data[ATTR_CURRENT_LONGITUDE]

    return _set_location(opp, data, location_name)


def _is_mobile_beacon(data, mobile_beacons):
    """Check if we have a mobile beacon."""
    return ATTR_BEACON_ID in data and data["name"] in mobile_beacons


def _device_name(data):
    """Return name of device tracker."""
    if ATTR_BEACON_ID in data:
        return f"{BEACON_DEV_PREFIX}_{data['name']}"
    return data["device"]


def _set_location(opp, data, location_name):
    """Fire OP event to set location."""
    device = _device_name(data)

    async_dispatcher_send(
        opp,
        TRACKER_UPDATE,
        device,
        (data[ATTR_LATITUDE], data[ATTR_LONGITUDE]),
        location_name,
        data,
    )

    return web.Response(text=f"Setting location for {device}", status=HTTP_OK)


async def async_setup_entry(opp, entry):
    """Configure based on config entry."""
    opp.components.webhook.async_register(
        DOMAIN, "Geofency", entry.data[CONF_WEBHOOK_ID], handle_webhook
    )

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, DEVICE_TRACKER)
    )
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    opp.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    opp.data[DOMAIN]["unsub_device_tracker"].pop(entry.entry_id)()
    await opp.config_entries.async_forward_entry_unload(entry, DEVICE_TRACKER)
    return True


async_remove_entry = config_entry_flow.webhook_async_remove_entry
