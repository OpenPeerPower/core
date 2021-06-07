"""The openweathermap component."""
import logging

from pyowm import OWM
from pyowm.utils.config import get_default_config

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_NAME,
)
from openpeerpower.core import OpenPeerPower

from .const import (
    CONF_LANGUAGE,
    CONFIG_FLOW_VERSION,
    DOMAIN,
    ENTRY_NAME,
    ENTRY_WEATHER_COORDINATOR,
    FORECAST_MODE_FREE_DAILY,
    FORECAST_MODE_ONECALL_DAILY,
    PLATFORMS,
    UPDATE_LISTENER,
)
from .weather_update_coordinator import WeatherUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up OpenWeatherMap as config entry."""
    name = entry.data[CONF_NAME]
    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data.get(CONF_LATITUDE, opp.config.latitude)
    longitude = entry.data.get(CONF_LONGITUDE, opp.config.longitude)
    forecast_mode = _get_config_value(entry, CONF_MODE)
    language = _get_config_value(entry, CONF_LANGUAGE)

    config_dict = _get_owm_config(language)

    owm = OWM(api_key, config_dict).weather_manager()
    weather_coordinator = WeatherUpdateCoordinator(
        owm, latitude, longitude, forecast_mode,.opp
    )

    await weather_coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        ENTRY_NAME: name,
        ENTRY_WEATHER_COORDINATOR: weather_coordinator,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    update_listener = entry.add_update_listener(async_update_options)
    opp.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_migrate_entry(opp, entry):
    """Migrate old entry."""
    config_entries = opp.config_entries
    data = entry.data
    version = entry.version

    _LOGGER.debug("Migrating OpenWeatherMap entry from version %s", version)

    if version == 1:
        mode = data[CONF_MODE]
        if mode == FORECAST_MODE_FREE_DAILY:
            mode = FORECAST_MODE_ONECALL_DAILY

        new_data = {**data, CONF_MODE: mode}
        version = entry.version = CONFIG_FLOW_VERSION
        config_entries.async_update_entry(entry, data=new_data)

    _LOGGER.info("Migration to version %s successful", version)

    return True


async def async_update_options(opp: OpenPeerPower, entry: ConfigEntry):
    """Update options."""
    await opp.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        update_listener = opp.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _filter_domain_configs(elements, domain):
    return list(filter(lambda elem: elem["platform"] == domain, elements))


def _get_config_value(config_entry, key):
    if config_entry.options:
        return config_entry.options[key]
    return config_entry.data[key]


def _get_owm_config(language):
    """Get OpenWeatherMap configuration and add language to it."""
    config_dict = get_default_config()
    config_dict["language"] = language
    return config_dict
