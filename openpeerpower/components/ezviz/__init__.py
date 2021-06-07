"""Support for Ezviz camera."""
from datetime import timedelta
import logging

from pyezviz.client import EzvizClient, HTTPError, InvalidURL, PyEzvizError

from openpeerpower.const import (
    CONF_PASSWORD,
    CONF_TIMEOUT,
    CONF_TYPE,
    CONF_URL,
    CONF_USERNAME,
)
from openpeerpower.exceptions import ConfigEntryNotReady

from .const import (
    ATTR_TYPE_CAMERA,
    ATTR_TYPE_CLOUD,
    CONF_FFMPEG_ARGUMENTS,
    DATA_COORDINATOR,
    DATA_UNDO_UPDATE_LISTENER,
    DEFAULT_FFMPEG_ARGUMENTS,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .coordinator import EzvizDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

PLATFORMS = [
    "binary_sensor",
    "camera",
    "sensor",
    "switch",
]


async def async_setup_entry(opp, entry):
    """Set up Ezviz from a config entry."""
    opp.data.setdefault(DOMAIN, {})

    if not entry.options:
        options = {
            CONF_FFMPEG_ARGUMENTS: entry.data.get(
                CONF_FFMPEG_ARGUMENTS, DEFAULT_FFMPEG_ARGUMENTS
            ),
            CONF_TIMEOUT: entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        }
        opp.config_entries.async_update_entry(entry, options=options)

    if entry.data.get(CONF_TYPE) == ATTR_TYPE_CAMERA:
        if opp.data.get(DOMAIN):
            # Should only execute on addition of new camera entry.
            # Fetch Entry id of main account and reload it.
            for item in opp.config_entries.async_entries():
                if item.data.get(CONF_TYPE) == ATTR_TYPE_CLOUD:
                    _LOGGER.info("Reload Ezviz integration with new camera rtsp entry")
                    await opp.config_entries.async_reload(item.entry_id)

        return True

    try:
        ezviz_client = await opp.async_add_executor_job(
            _get_ezviz_client_instance, entry
        )
    except (InvalidURL, HTTPError, PyEzvizError) as error:
        _LOGGER.error("Unable to connect to Ezviz service: %s", str(error))
        raise ConfigEntryNotReady from error

    coordinator = EzvizDataUpdateCoordinator(opp, api=ezviz_client)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UNDO_UPDATE_LISTENER: undo_listener,
    }
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""

    if entry.data.get(CONF_TYPE) == ATTR_TYPE_CAMERA:
        return True

    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN][entry.entry_id][DATA_UNDO_UPDATE_LISTENER]()
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(opp, entry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


def _get_ezviz_client_instance(entry):
    """Initialize a new instance of EzvizClientApi."""
    ezviz_client = EzvizClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_URL],
        entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
    )
    ezviz_client.login()
    return ezviz_client
