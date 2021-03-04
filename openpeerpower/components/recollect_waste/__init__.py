"""The ReCollect Waste integration."""
import asyncio
from datetime import date, timedelta
from typing import List

from aiorecollect.client import Client, PickupEvent
from aiorecollect.errors import RecollectError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_PLACE_ID, CONF_SERVICE_ID, DATA_COORDINATOR, DOMAIN, LOGGER

DATA_LISTENER = "listener"

DEFAULT_NAME = "recollect_waste"
DEFAULT_UPDATE_INTERVAL = timedelta(days=1)

PLATFORMS = ["sensor"]


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up the RainMachine component."""
    opp.data[DOMAIN] = {DATA_COORDINATOR: {}, DATA_LISTENER: {}}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up RainMachine as config entry."""
    session = aiohttp_client.async_get_clientsession(opp)
    client = Client(
        entry.data[CONF_PLACE_ID], entry.data[CONF_SERVICE_ID], session=session
    )

    async def async_get_pickup_events() -> List[PickupEvent]:
        """Get the next pickup."""
        try:
            return await client.async_get_pickup_events(
                start_date=date.today(), end_date=date.today() + timedelta(weeks=4)
            )
        except RecollectError as err:
            raise UpdateFailed(
                f"Error while requesting data from ReCollect: {err}"
            ) from err

    coordinator = DataUpdateCoordinator(
        opp,
        LOGGER,
        name=f"Place {entry.data[CONF_PLACE_ID]}, Service {entry.data[CONF_SERVICE_ID]}",
        update_interval=DEFAULT_UPDATE_INTERVAL,
        update_method=async_get_pickup_events,
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data[DOMAIN][DATA_COORDINATOR][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    opp.data[DOMAIN][DATA_LISTENER][entry.entry_id] = entry.add_update_listener(
        async_reload_entry
    )

    return True


async def async_reload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle an options update."""
    await opp.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload an RainMachine config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN][DATA_COORDINATOR].pop(entry.entry_id)
        cancel_listener = opp.data[DOMAIN][DATA_LISTENER].pop(entry.entry_id)
        cancel_listener()

    return unload_ok
