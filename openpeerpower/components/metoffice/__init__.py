"""The Met Office integration."""

import asyncio
import logging

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    METOFFICE_COORDINATOR,
    METOFFICE_DATA,
    METOFFICE_NAME,
)
from .data import MetOfficeData

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "weather"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Met Office weather component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up a Met Office entry."""

    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    api_key = entry.data[CONF_API_KEY]
    site_name = entry.data[CONF_NAME]

    metoffice_data = MetOfficeData(opp, api_key, latitude, longitude)
    await metoffice_data.async_update_site()
    if metoffice_data.site_name is None:
        raise ConfigEntryNotReady()

    metoffice_coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=f"MetOffice Coordinator for {site_name}",
        update_method=metoffice_data.async_update,
        update_interval=DEFAULT_SCAN_INTERVAL,
    )

    metoffice_opp_data = opp.data.setdefault(DOMAIN, {})
    metoffice_opp_data[entry.entry_id] = {
        METOFFICE_DATA: metoffice_data,
        METOFFICE_COORDINATOR: metoffice_coordinator,
        METOFFICE_NAME: site_name,
    }

    # Fetch initial data so we have data when entities subscribe
    await metoffice_coordinator.async_refresh()
    if metoffice_data.now is None:
        raise ConfigEntryNotReady()

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
        opp.data[DOMAIN].pop(entry.entry_id)
        if not opp.data[DOMAIN]:
            opp.data.pop(DOMAIN)
    return unload_ok
