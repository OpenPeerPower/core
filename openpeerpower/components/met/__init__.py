"""The met component."""
from datetime import timedelta
import logging
from random import randrange

import metno

from openpeerpower.const import (
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    EVENT_CORE_CONFIG_UPDATE,
    LENGTH_FEET,
    LENGTH_METERS,
)
from openpeerpower.core import Config, OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from openpeerpower.util.distance import convert as convert_distance
import openpeerpower.util.dt as dt_util

from .const import CONF_TRACK_HOME, DOMAIN

URL = "https://aa015h6buqvih86i1.api.met.no/weatherapi/locationforecast/2.0/complete"


_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up configured Met."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp, config_entry):
    """Set up Met as config entry."""
    coordinator = MetDataUpdateCoordinator(opp, config_entry)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    if config_entry.data.get(CONF_TRACK_HOME, False):
        coordinator.track_home()

    opp.data[DOMAIN][config_entry.entry_id] = coordinator

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, "weather")
    )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    await opp.config_entries.async_forward_entry_unload(config_entry, "weather")
    opp.data[DOMAIN][config_entry.entry_id].untrack_home()
    opp.data[DOMAIN].pop(config_entry.entry_id)

    return True


class MetDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Met data."""

    def __init__(self, opp, config_entry):
        """Initialize global Met data updater."""
        self._unsub_track_home = None
        self.weather = MetWeatherData(
            opp, config_entry.data, opp.config.units.is_metric
        )
        self.weather.init_data()

        update_interval = timedelta(minutes=randrange(55, 65))

        super().__init__(opp, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Fetch data from Met."""
        try:
            return await self.weather.fetch_data()
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}") from err

    def track_home(self):
        """Start tracking changes to OP home setting."""
        if self._unsub_track_home:
            return

        async def _async_update_weather_data(_event=None):
            """Update weather data."""
            self.weather.init_data()
            await self.async_refresh()

        self._unsub_track_home = self.opp.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE, _async_update_weather_data
        )

    def untrack_home(self):
        """Stop tracking changes to OP home setting."""
        if self._unsub_track_home:
            self._unsub_track_home()
            self._unsub_track_home = None


class MetWeatherData:
    """Keep data for Met.no weather entities."""

    def __init__(self, opp, config, is_metric):
        """Initialise the weather entity data."""
        self.opp = opp
        self._config = config
        self._is_metric = is_metric
        self._weather_data = None
        self.current_weather_data = {}
        self.daily_forecast = None
        self.hourly_forecast = None

    def init_data(self):
        """Weather data inialization - get the coordinates."""
        if self._config.get(CONF_TRACK_HOME, False):
            latitude = self.opp.config.latitude
            longitude = self.opp.config.longitude
            elevation = self.opp.config.elevation
        else:
            latitude = self._config[CONF_LATITUDE]
            longitude = self._config[CONF_LONGITUDE]
            elevation = self._config[CONF_ELEVATION]

        if not self._is_metric:
            elevation = int(
                round(convert_distance(elevation, LENGTH_FEET, LENGTH_METERS))
            )

        coordinates = {
            "lat": str(latitude),
            "lon": str(longitude),
            "msl": str(elevation),
        }

        self._weather_data = metno.MetWeatherData(
            coordinates, async_get_clientsession(self.opp), api_url=URL
        )

    async def fetch_data(self):
        """Fetch data from API - (current weather and forecast)."""
        await self._weather_data.fetching_data()
        self.current_weather_data = self._weather_data.get_current_weather()
        time_zone = dt_util.DEFAULT_TIME_ZONE
        self.daily_forecast = self._weather_data.get_forecast(time_zone, False)
        self.hourly_forecast = self._weather_data.get_forecast(time_zone, True)
        return self
