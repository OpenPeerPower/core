"""The AccuWeather component."""
import asyncio
from datetime import timedelta
import logging

from accuweather import AccuWeather, ApiError, InvalidApiKeyError, RequestsExceededError
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout

from openpeerpower.const import CONF_API_KEY
from openpeerpower.core import Config, OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_FORECAST,
    CONF_FORECAST,
    COORDINATOR,
    DOMAIN,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "weather"]


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up configured AccuWeather."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp, config_entry) -> bool:
    """Set up AccuWeather as config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    location_key = config_entry.unique_id
    forecast = config_entry.options.get(CONF_FORECAST, False)

    _LOGGER.debug("Using location_key: %s, get forecast: %s", location_key, forecast)

    websession = async_get_clientsession(opp)

    coordinator = AccuWeatherDataUpdateCoordinator(
        opp, websession, api_key, location_key, forecast
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = config_entry.add_update_listener(update_listener)

    opp.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    opp.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(opp, config_entry):
    """Update listener."""
    await opp.config_entries.async_reload(config_entry.entry_id)


class AccuWeatherDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching AccuWeather data API."""

    def __init__(self, opp, session, api_key, location_key, forecast: bool):
        """Initialize."""
        self.location_key = location_key
        self.forecast = forecast
        self.is_metric = opp.config.units.is_metric
        self.accuweather = AccuWeather(api_key, session, location_key=self.location_key)

        # Enabling the forecast download increases the number of requests per data
        # update, we use 40 minutes for current condition only and 80 minutes for
        # current condition and forecast as update interval to not exceed allowed number
        # of requests. We have 50 requests allowed per day, so we use 36 and leave 14 as
        # a reserve for restarting HA.
        update_interval = timedelta(minutes=40)
        if self.forecast:
            update_interval *= 2
        _LOGGER.debug("Data will be update every %s", update_interval)

        super().__init__(opp, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with timeout(10):
                current = await self.accuweather.async_get_current_conditions()
                forecast = (
                    await self.accuweather.async_get_forecast(metric=self.is_metric)
                    if self.forecast
                    else {}
                )
        except (
            ApiError,
            ClientConnectorError,
            InvalidApiKeyError,
            RequestsExceededError,
        ) as error:
            raise UpdateFailed(error) from error
        _LOGGER.debug("Requests remaining: %s", self.accuweather.requests_remaining)
        return {**current, **{ATTR_FORECAST: forecast}}
