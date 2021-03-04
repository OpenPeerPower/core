"""Support for Canary devices."""
import asyncio
from datetime import timedelta
import logging

from canary.api import Api
from requests import ConnectTimeout, HTTPError
import voluptuous as vol

from openpeerpower.components.camera.const import DOMAIN as CAMERA_DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_TIMEOUT, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import (
    CONF_FFMPEG_ARGUMENTS,
    DATA_COORDINATOR,
    DATA_UNDO_UPDATE_LISTENER,
    DEFAULT_FFMPEG_ARGUMENTS,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .coordinator import CanaryDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["alarm_control_panel", "camera", "sensor"]


async def async_setup(opp: OpenPeerPowerType, config: dict) -> bool:
    """Set up the Canary integration."""
    opp.data.setdefault(DOMAIN, {})

    if opp.config_entries.async_entries(DOMAIN):
        return True

    ffmpeg_arguments = DEFAULT_FFMPEG_ARGUMENTS
    if CAMERA_DOMAIN in config:
        camera_config = next(
            (item for item in config[CAMERA_DOMAIN] if item["platform"] == DOMAIN),
            None,
        )

        if camera_config:
            ffmpeg_arguments = camera_config.get(
                CONF_FFMPEG_ARGUMENTS, DEFAULT_FFMPEG_ARGUMENTS
            )

    if DOMAIN in config:
        if ffmpeg_arguments != DEFAULT_FFMPEG_ARGUMENTS:
            config[DOMAIN][CONF_FFMPEG_ARGUMENTS] = ffmpeg_arguments

        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up Canary from a config entry."""
    if not entry.options:
        options = {
            CONF_FFMPEG_ARGUMENTS: entry.data.get(
                CONF_FFMPEG_ARGUMENTS, DEFAULT_FFMPEG_ARGUMENTS
            ),
            CONF_TIMEOUT: entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        }
        opp.config_entries.async_update_entry(entry, options=options)

    try:
        canary_api = await opp.async_add_executor_job(_get_canary_api_instance, entry)
    except (ConnectTimeout, HTTPError) as error:
        _LOGGER.error("Unable to connect to Canary service: %s", str(error))
        raise ConfigEntryNotReady from error

    coordinator = CanaryDataUpdateCoordinator(opp, api=canary_api)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
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
        opp.data[DOMAIN][entry.entry_id][DATA_UNDO_UPDATE_LISTENER]()
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_update_listener(opp: OpenPeerPowerType, entry: ConfigEntry) -> None:
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


def _get_canary_api_instance(entry: ConfigEntry) -> Api:
    """Initialize a new instance of CanaryApi."""
    canary = Api(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
    )

    return canary
