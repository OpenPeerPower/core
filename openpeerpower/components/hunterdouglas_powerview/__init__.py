"""The Hunter Douglas PowerView integration."""
import asyncio
from datetime import timedelta
import logging

from aiopvapi.helpers.aiorequest import AioRequest
from aiopvapi.helpers.constants import ATTR_ID
from aiopvapi.helpers.tools import base64_to_unicode
from aiopvapi.rooms import Rooms
from aiopvapi.scenes import Scenes
from aiopvapi.shades import Shades
from aiopvapi.userdata import UserData
import async_timeout

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    COORDINATOR,
    DEVICE_FIRMWARE,
    DEVICE_INFO,
    DEVICE_MAC_ADDRESS,
    DEVICE_MODEL,
    DEVICE_NAME,
    DEVICE_REVISION,
    DEVICE_SERIAL_NUMBER,
    DOMAIN,
    FIRMWARE_BUILD,
    FIRMWARE_IN_USERDATA,
    FIRMWARE_SUB_REVISION,
    HUB_EXCEPTIONS,
    HUB_NAME,
    LEGACY_DEVICE_BUILD,
    LEGACY_DEVICE_MODEL,
    LEGACY_DEVICE_REVISION,
    LEGACY_DEVICE_SUB_REVISION,
    MAC_ADDRESS_IN_USERDATA,
    MAINPROCESSOR_IN_USERDATA_FIRMWARE,
    MODEL_IN_MAINPROCESSOR,
    PV_API,
    PV_ROOM_DATA,
    PV_SCENE_DATA,
    PV_SHADE_DATA,
    PV_SHADES,
    REVISION_IN_MAINPROCESSOR,
    ROOM_DATA,
    SCENE_DATA,
    SERIAL_NUMBER_IN_USERDATA,
    SHADE_DATA,
    USER_DATA,
)

PARALLEL_UPDATES = 1

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

PLATFORMS = ["cover", "scene", "sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, opp_config: dict):
    """Set up the Hunter Douglas PowerView component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Hunter Douglas PowerView from a config entry."""

    config = entry.data

    hub_address = config.get(CONF_HOST)
    websession = async_get_clientsession(opp)

    pv_request = AioRequest(hub_address, loop=opp.loop, websession=websession)

    try:
        async with async_timeout.timeout(10):
            device_info = await async_get_device_info(pv_request)

        async with async_timeout.timeout(10):
            rooms = Rooms(pv_request)
            room_data = _async_map_data_by_id((await rooms.get_resources())[ROOM_DATA])

        async with async_timeout.timeout(10):
            scenes = Scenes(pv_request)
            scene_data = _async_map_data_by_id(
                (await scenes.get_resources())[SCENE_DATA]
            )

        async with async_timeout.timeout(10):
            shades = Shades(pv_request)
            shade_data = _async_map_data_by_id(
                (await shades.get_resources())[SHADE_DATA]
            )
    except HUB_EXCEPTIONS as err:
        _LOGGER.error("Connection error to PowerView hub: %s", hub_address)
        raise ConfigEntryNotReady from err

    if not device_info:
        _LOGGER.error("Unable to initialize PowerView hub: %s", hub_address)
        raise ConfigEntryNotReady

    async def async_update_data():
        """Fetch data from shade endpoint."""
        async with async_timeout.timeout(10):
            shade_entries = await shades.get_resources()
        if not shade_entries:
            raise UpdateFailed("Failed to fetch new shade data.")
        return _async_map_data_by_id(shade_entries[SHADE_DATA])

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="powerview hub",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )

    opp.data[DOMAIN][entry.entry_id] = {
        PV_API: pv_request,
        PV_ROOM_DATA: room_data,
        PV_SCENE_DATA: scene_data,
        PV_SHADES: shades,
        PV_SHADE_DATA: shade_data,
        COORDINATOR: coordinator,
        DEVICE_INFO: device_info,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_get_device_info(pv_request):
    """Determine device info."""
    userdata = UserData(pv_request)
    resources = await userdata.get_resources()
    userdata_data = resources[USER_DATA]

    if FIRMWARE_IN_USERDATA in userdata_data:
        main_processor_info = userdata_data[FIRMWARE_IN_USERDATA][
            MAINPROCESSOR_IN_USERDATA_FIRMWARE
        ]
    else:
        # Legacy devices
        main_processor_info = {
            REVISION_IN_MAINPROCESSOR: LEGACY_DEVICE_REVISION,
            FIRMWARE_SUB_REVISION: LEGACY_DEVICE_SUB_REVISION,
            FIRMWARE_BUILD: LEGACY_DEVICE_BUILD,
            MODEL_IN_MAINPROCESSOR: LEGACY_DEVICE_MODEL,
        }

    return {
        DEVICE_NAME: base64_to_unicode(userdata_data[HUB_NAME]),
        DEVICE_MAC_ADDRESS: userdata_data[MAC_ADDRESS_IN_USERDATA],
        DEVICE_SERIAL_NUMBER: userdata_data[SERIAL_NUMBER_IN_USERDATA],
        DEVICE_REVISION: main_processor_info[REVISION_IN_MAINPROCESSOR],
        DEVICE_FIRMWARE: main_processor_info,
        DEVICE_MODEL: main_processor_info[MODEL_IN_MAINPROCESSOR],
    }


@callback
def _async_map_data_by_id(data):
    """Return a dict with the key being the id for a list of entries."""
    return {entry[ATTR_ID]: entry for entry in data}


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
