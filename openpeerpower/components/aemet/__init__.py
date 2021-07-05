"""The AEMET OpenData component."""
import logging

from aemet_opendata.interface import AEMET

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.core import OpenPeerPower

from .const import (
    CONF_STATION_UPDATES,
    DOMAIN,
    ENTRY_NAME,
    ENTRY_WEATHER_COORDINATOR,
    PLATFORMS,
)
from .weather_update_coordinator import WeatherUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Set up AEMET OpenData as config entry."""
    name = config_entry.data[CONF_NAME]
    api_key = config_entry.data[CONF_API_KEY]
    latitude = config_entry.data[CONF_LATITUDE]
    longitude = config_entry.data[CONF_LONGITUDE]
    station_updates = config_entry.options.get(CONF_STATION_UPDATES, True)

    aemet = AEMET(api_key)
    weather_coordinator = WeatherUpdateCoordinator(
        opp, aemet, latitude, longitude, station_updates
    )

    await weather_coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][config_entry.entry_id] = {
        ENTRY_NAME: name,
        ENTRY_WEATHER_COORDINATOR: weather_coordinator,
    }

    opp.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))

    return True


async def async_update_options(opp: OpenPeerPower, config_entry: ConfigEntry) -> None:
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
