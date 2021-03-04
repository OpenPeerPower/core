"""The AEMET OpenData component."""
import asyncio
import logging

from aemet_opendata.interface import AEMET

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.core import OpenPeerPower

from .const import DOMAIN, ENTRY_NAME, ENTRY_WEATHER_COORDINATOR, PLATFORMS
from .weather_update_coordinator import WeatherUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up the AEMET OpenData component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Set up AEMET OpenData as config entry."""
    name = config_entry.data[CONF_NAME]
    api_key = config_entry.data[CONF_API_KEY]
    latitude = config_entry.data[CONF_LATITUDE]
    longitude = config_entry.data[CONF_LONGITUDE]

    aemet = AEMET(api_key)
    weather_coordinator = WeatherUpdateCoordinator(opp, aemet, latitude, longitude)

    await weather_coordinator.async_refresh()

    opp.data[DOMAIN][config_entry.entry_id] = {
        ENTRY_NAME: name,
        ENTRY_WEATHER_COORDINATOR: weather_coordinator,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
