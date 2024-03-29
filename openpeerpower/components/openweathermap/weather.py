"""Support for the OpenWeatherMap (OWM) service."""
from openpeerpower.components.weather import WeatherEntity
from openpeerpower.const import PRESSURE_HPA, PRESSURE_INHG, TEMP_CELSIUS
from openpeerpower.util.pressure import convert as pressure_convert

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_FORECAST,
    ATTR_API_HUMIDITY,
    ATTR_API_PRESSURE,
    ATTR_API_TEMPERATURE,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_SPEED,
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN,
    ENTRY_NAME,
    ENTRY_WEATHER_COORDINATOR,
    MANUFACTURER,
)
from .weather_update_coordinator import WeatherUpdateCoordinator


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up OpenWeatherMap weather entity based on a config entry."""
    domain_data = opp.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    weather_coordinator = domain_data[ENTRY_WEATHER_COORDINATOR]

    unique_id = f"{config_entry.unique_id}"
    owm_weather = OpenWeatherMapWeather(name, unique_id, weather_coordinator)

    async_add_entities([owm_weather], False)


class OpenWeatherMapWeather(WeatherEntity):
    """Implementation of an OpenWeatherMap sensor."""

    def __init__(
        self,
        name,
        unique_id,
        weather_coordinator: WeatherUpdateCoordinator,
    ):
        """Initialize the sensor."""
        self._name = name
        self._unique_id = unique_id
        self._weather_coordinator = weather_coordinator

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": DEFAULT_NAME,
            "manufacturer": MANUFACTURER,
            "entry_type": "service",
        }

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def condition(self):
        """Return the current condition."""
        return self._weather_coordinator.data[ATTR_API_CONDITION]

    @property
    def temperature(self):
        """Return the temperature."""
        return self._weather_coordinator.data[ATTR_API_TEMPERATURE]

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def pressure(self):
        """Return the pressure."""
        pressure = self._weather_coordinator.data[ATTR_API_PRESSURE]
        # OpenWeatherMap returns pressure in hPA, so convert to
        # inHg if we aren't using metric.
        if not self.opp.config.units.is_metric and pressure:
            return pressure_convert(pressure, PRESSURE_HPA, PRESSURE_INHG)
        return pressure

    @property
    def humidity(self):
        """Return the humidity."""
        return self._weather_coordinator.data[ATTR_API_HUMIDITY]

    @property
    def wind_speed(self):
        """Return the wind speed."""
        wind_speed = self._weather_coordinator.data[ATTR_API_WIND_SPEED]
        if self.opp.config.units.name == "imperial":
            return round(wind_speed * 2.24, 2)
        return round(wind_speed * 3.6, 2)

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self._weather_coordinator.data[ATTR_API_WIND_BEARING]

    @property
    def forecast(self):
        """Return the forecast array."""
        return self._weather_coordinator.data[ATTR_API_FORECAST]

    @property
    def available(self):
        """Return True if entity is available."""
        return self._weather_coordinator.last_update_success

    async def async_added_to_opp(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._weather_coordinator.async_add_listener(self.async_write_op_state)
        )

    async def async_update(self):
        """Get the latest data from OWM and updates the states."""
        await self._weather_coordinator.async_request_refresh()
