"""The Dexcom integration."""
import asyncio
from datetime import timedelta
import logging

from pydexcom import AccountError, Dexcom, SessionError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_UNIT_OF_MEASUREMENT, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SERVER,
    COORDINATOR,
    DOMAIN,
    MG_DL,
    PLATFORMS,
    SERVER_OUS,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=180)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up configured Dexcom."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Dexcom from a config entry."""
    try:
        dexcom = await opp.async_add_executor_job(
            Dexcom,
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data[CONF_SERVER] == SERVER_OUS,
        )
    except AccountError:
        return False
    except SessionError as error:
        raise ConfigEntryNotReady from error

    if not entry.options:
        opp.config_entries.async_update_entry(
            entry, options={CONF_UNIT_OF_MEASUREMENT: MG_DL}
        )

    async def async_update_data():
        try:
            return await opp.async_add_executor_job(dexcom.get_current_glucose_reading)
        except SessionError as error:
            raise UpdateFailed(error) from error

    opp.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: DataUpdateCoordinator(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_method=async_update_data,
            update_interval=SCAN_INTERVAL,
        ),
        UNDO_UPDATE_LISTENER: entry.add_update_listener(update_listener),
    }

    await opp.data[DOMAIN][entry.entry_id][COORDINATOR].async_refresh()

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
    opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(opp, entry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)
