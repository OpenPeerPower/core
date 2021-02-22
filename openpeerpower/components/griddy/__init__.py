"""The Griddy Power integration."""
import asyncio
from datetime import timedelta
import logging

from griddypower.async_api import LOAD_ZONES, AsyncGriddy
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_LOADZONE, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_LOADZONE): vol.In(LOAD_ZONES)})},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["sensor"]


async def async_setup_opp: OpenPeerPower, config: dict):
    """Set up the Griddy Power component."""

    opp.data.setdefault(DOMAIN, {})
    conf = config.get(DOMAIN)

    if not conf:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_LOADZONE: conf.get(CONF_LOADZONE)},
        )
    )
    return True


async def async_setup_entry.opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Griddy Power from a config entry."""

    entry_data = entry.data

    async_griddy = AsyncGriddy(
        aiohttp_client.async_get_clientsession.opp),
        settlement_point=entry_data[CONF_LOADZONE],
    )

    async def async_update_data():
        """Fetch data from API endpoint."""
        return await async_griddy.async_getnow()

    coordinator = DataUpdateCoordinator(
        opp.
        _LOGGER,
        name="Griddy getnow",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry.opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
