"""The Tile component."""
import asyncio
from datetime import timedelta
from functools import partial

from pytile import async_login
from pytile.errors import InvalidAuthError, SessionExpiredError, TileError

from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from openpeerpower.util.async_ import gather_with_concurrency

from .const import DATA_COORDINATOR, DATA_TILE, DOMAIN, LOGGER

PLATFORMS = ["device_tracker"]
DEVICE_TYPES = ["PHONE", "TILE"]

DEFAULT_INIT_TASK_LIMIT = 2
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=2)

CONF_SHOW_INACTIVE = "show_inactive"


async def async_setup(opp, config):
    """Set up the Tile component."""
    opp.data[DOMAIN] = {DATA_COORDINATOR: {}, DATA_TILE: {}}
    return True


async def async_setup_entry(opp, entry):
    """Set up Tile as config entry."""
    opp.data[DOMAIN][DATA_COORDINATOR][entry.entry_id] = {}
    opp.data[DOMAIN][DATA_TILE][entry.entry_id] = {}

    websession = aiohttp_client.async_get_clientsession(opp)

    try:
        client = await async_login(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            session=websession,
        )
        opp.data[DOMAIN][DATA_TILE][entry.entry_id] = await client.async_get_tiles()
    except InvalidAuthError:
        LOGGER.error("Invalid credentials provided")
        return False
    except TileError as err:
        raise ConfigEntryNotReady("Error during integration setup") from err

    async def async_update_tile(tile):
        """Update the Tile."""
        try:
            return await tile.async_update()
        except SessionExpiredError:
            LOGGER.info("Tile session expired; creating a new one")
            await client.async_init()
        except TileError as err:
            raise UpdateFailed(f"Error while retrieving data: {err}") from err

    coordinator_init_tasks = []
    for tile_uuid, tile in opp.data[DOMAIN][DATA_TILE][entry.entry_id].items():
        coordinator = opp.data[DOMAIN][DATA_COORDINATOR][entry.entry_id][
            tile_uuid
        ] = DataUpdateCoordinator(
            opp,
            LOGGER,
            name=tile.name,
            update_interval=DEFAULT_UPDATE_INTERVAL,
            update_method=partial(async_update_tile, tile),
        )
        coordinator_init_tasks.append(coordinator.async_refresh())

    await gather_with_concurrency(DEFAULT_INIT_TASK_LIMIT, *coordinator_init_tasks)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp, entry):
    """Unload a Tile config entry."""
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

    return unload_ok
