"""Support for Meteo-France weather data."""
import asyncio
from datetime import timedelta
import logging

from meteofrance_api.client import MeteoFranceClient
from meteofrance_api.helpers import is_valid_warning_department
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CITY,
    COORDINATOR_ALERT,
    COORDINATOR_FORECAST,
    COORDINATOR_RAIN,
    DOMAIN,
    PLATFORMS,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_RAIN = timedelta(minutes=5)
SCAN_INTERVAL = timedelta(minutes=15)


CITY_SCHEMA = vol.Schema({vol.Required(CONF_CITY): cv.string})

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [CITY_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Set up Meteo-France from legacy config file."""
    conf = config.get(DOMAIN)
    if not conf:
        return True

    for city_conf in conf:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=city_conf
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up an Meteo-France account from a config entry."""
    opp.data.setdefault(DOMAIN, {})

    latitude = entry.data.get(CONF_LATITUDE)

    client = MeteoFranceClient()
    # Migrate from previous config
    if not latitude:
        places = await opp.async_add_executor_job(
            client.search_places, entry.data[CONF_CITY]
        )
        opp.config_entries.async_update_entry(
            entry,
            title=f"{places[0]}",
            data={
                CONF_LATITUDE: places[0].latitude,
                CONF_LONGITUDE: places[0].longitude,
            },
        )

    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    async def _async_update_data_forecast_forecast():
        """Fetch data from API endpoint."""
        return await opp.async_add_executor_job(
            client.get_forecast, latitude, longitude
        )

    async def _async_update_data_rain():
        """Fetch data from API endpoint."""
        return await opp.async_add_executor_job(client.get_rain, latitude, longitude)

    async def _async_update_data_alert():
        """Fetch data from API endpoint."""
        return await opp.async_add_executor_job(
            client.get_warning_current_phenomenoms, department, 0, True
        )

    coordinator_forecast = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=f"Météo-France forecast for city {entry.title}",
        update_method=_async_update_data_forecast_forecast,
        update_interval=SCAN_INTERVAL,
    )
    coordinator_rain = None
    coordinator_alert = None

    # Fetch initial data so we have data when entities subscribe
    await coordinator_forecast.async_refresh()

    if not coordinator_forecast.last_update_success:
        raise ConfigEntryNotReady

    # Check if rain forecast is available.
    if coordinator_forecast.data.position.get("rain_product_available") == 1:
        coordinator_rain = DataUpdateCoordinator(
            opp,
            _LOGGER,
            name=f"Météo-France rain for city {entry.title}",
            update_method=_async_update_data_rain,
            update_interval=SCAN_INTERVAL_RAIN,
        )
        await coordinator_rain.async_refresh()

        if not coordinator_rain.last_update_success:
            raise ConfigEntryNotReady
    else:
        _LOGGER.warning(
            "1 hour rain forecast not available. %s is not in covered zone",
            entry.title,
        )

    department = coordinator_forecast.data.position.get("dept")
    _LOGGER.debug(
        "Department corresponding to %s is %s",
        entry.title,
        department,
    )
    if is_valid_warning_department(department):
        if not opp.data[DOMAIN].get(department):
            coordinator_alert = DataUpdateCoordinator(
                opp,
                _LOGGER,
                name=f"Météo-France alert for department {department}",
                update_method=_async_update_data_alert,
                update_interval=SCAN_INTERVAL,
            )

            await coordinator_alert.async_refresh()

            if not coordinator_alert.last_update_success:
                raise ConfigEntryNotReady

            opp.data[DOMAIN][department] = True
        else:
            _LOGGER.warning(
                "Weather alert for department %s won't be added with city %s, as it has already been added within another city",
                department,
                entry.title,
            )
    else:
        _LOGGER.warning(
            "Weather alert not available: The city %s is not in metropolitan France or Andorre.",
            entry.title,
        )

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        COORDINATOR_FORECAST: coordinator_forecast,
        COORDINATOR_RAIN: coordinator_rain,
        COORDINATOR_ALERT: coordinator_alert,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Unload a config entry."""
    if opp.data[DOMAIN][entry.entry_id][COORDINATOR_ALERT]:

        department = opp.data[DOMAIN][entry.entry_id][
            COORDINATOR_FORECAST
        ].data.position.get("dept")
        opp.data[DOMAIN][department] = False
        _LOGGER.debug(
            "Weather alert for depatment %s unloaded and released. It can be added now by another city.",
            department,
        )

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
        if not opp.data[DOMAIN]:
            opp.data.pop(DOMAIN)

    return unload_ok


async def _async_update_listener(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)
