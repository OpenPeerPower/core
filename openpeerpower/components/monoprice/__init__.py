"""The Monoprice 6-Zone Amplifier integration."""
import asyncio
import logging

from pymonoprice import get_monoprice
from serial import SerialException

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .const import (
    CONF_NOT_FIRST_RUN,
    DOMAIN,
    FIRST_RUN,
    MONOPRICE_OBJECT,
    UNDO_UPDATE_LISTENER,
)

PLATFORMS = ["media_player"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Monoprice 6-Zone Amplifier component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Monoprice 6-Zone Amplifier from a config entry."""
    port = entry.data[CONF_PORT]

    try:
        monoprice = await opp.async_add_executor_job(get_monoprice, port)
    except SerialException as err:
        _LOGGER.error("Error connecting to Monoprice controller at %s", port)
        raise ConfigEntryNotReady from err

    # double negative to handle absence of value
    first_run = not bool(entry.data.get(CONF_NOT_FIRST_RUN))

    if first_run:
        opp.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_NOT_FIRST_RUN: True}
        )

    undo_listener = entry.add_update_listener(_update_listener)

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        MONOPRICE_OBJECT: monoprice,
        UNDO_UPDATE_LISTENER: undo_listener,
        FIRST_RUN: first_run,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


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
        opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)
