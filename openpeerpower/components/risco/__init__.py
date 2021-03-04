"""The Risco integration."""
import asyncio
from datetime import timedelta
import logging

from pyrisco import CannotConnectError, OperationError, RiscoAPI, UnauthorizedError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_PASSWORD,
    CONF_PIN,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.storage import Store
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DEFAULT_SCAN_INTERVAL, DOMAIN, EVENTS_COORDINATOR

PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor"]
UNDO_UPDATE_LISTENER = "undo_update_listener"
LAST_EVENT_STORAGE_VERSION = 1
LAST_EVENT_TIMESTAMP_KEY = "last_event_timestamp"
_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Risco component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Risco from a config entry."""
    data = entry.data
    risco = RiscoAPI(data[CONF_USERNAME], data[CONF_PASSWORD], data[CONF_PIN])
    try:
        await risco.login(async_get_clientsession(opp))
    except CannotConnectError as error:
        raise ConfigEntryNotReady() from error
    except UnauthorizedError:
        _LOGGER.exception("Failed to login to Risco cloud")
        return False

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = RiscoDataUpdateCoordinator(opp, risco, scan_interval)
    await coordinator.async_refresh()
    events_coordinator = RiscoEventsDataUpdateCoordinator(
        opp, risco, entry.entry_id, 60
    )

    undo_listener = entry.add_update_listener(_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
        EVENTS_COORDINATOR: events_coordinator,
    }

    async def start_platforms():
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_setup(entry, platform)
                for platform in PLATFORMS
            ]
        )
        await events_coordinator.async_refresh()

    opp.async_create_task(start_platforms())

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


class RiscoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching risco data."""

    def __init__(self, opp, risco, scan_interval):
        """Initialize global risco data updater."""
        self.risco = risco
        interval = timedelta(seconds=scan_interval)
        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )

    async def _async_update_data(self):
        """Fetch data from risco."""
        try:
            return await self.risco.get_state()
        except (CannotConnectError, UnauthorizedError, OperationError) as error:
            raise UpdateFailed(error) from error


class RiscoEventsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching risco data."""

    def __init__(self, opp, risco, eid, scan_interval):
        """Initialize global risco data updater."""
        self.risco = risco
        self._store = Store(
            opp, LAST_EVENT_STORAGE_VERSION, f"risco_{eid}_last_event_timestamp"
        )
        interval = timedelta(seconds=scan_interval)
        super().__init__(
            opp,
            _LOGGER,
            name=f"{DOMAIN}_events",
            update_interval=interval,
        )

    async def _async_update_data(self):
        """Fetch data from risco."""
        last_store = await self._store.async_load() or {}
        last_timestamp = last_store.get(
            LAST_EVENT_TIMESTAMP_KEY, "2020-01-01T00:00:00Z"
        )
        try:
            events = await self.risco.get_events(last_timestamp, 10)
        except (CannotConnectError, UnauthorizedError, OperationError) as error:
            raise UpdateFailed(error) from error

        if len(events) > 0:
            await self._store.async_save({LAST_EVENT_TIMESTAMP_KEY: events[0].time})

        return events
