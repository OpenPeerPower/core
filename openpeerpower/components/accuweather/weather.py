"""Support for the AccuWeather service."""
from statistics import mean

from openpeerpower.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    WeatherEntity,
)
from openpeerpower.const import CONF_NAME, TEMP_CELSIUS, TEMP_FAHRENHEIT
from openpeerpower.helpers.update_coordinator import CoordinatorEntity
from openpeerpower.util.dt import utc_from_timestamp

from .const import (
    ATTR_FORECAST,
    ATTRIBUTION,
    CONDITION_CLASSES,
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    NAME,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Add a AccuWeather weather entity from a config_entry."""
    name = config_entry.data[CONF_NAME]

    coordinator = opp.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    async_add_entities([AccuWeatherEntity(name, coordinator)], False)


class AccuWeatherEntity(CoordinatorEntity, WeatherEntity):
    """Define an AccuWeather entity."""

    def __init__(self, name, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._name = name
        self._attrs = {}
        self._unit_system = "Metric" if self.coordinator.is_metric else "Imperial"

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self.coordinator.location_key

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.location_key)},
            "name": NAME,
            "manufacturer": MANUFACTURER,
            "entry_type": "service",
        }

    @property
    def condition(self):
        """Return the current condition."""
        try:
            return [
                k
                for k, v in CONDITION_CLASSES.items()
                if self.coordinator.data["WeatherIcon"] in v
            ][0]
        except IndexError:
            return None

    @property
    def temperature(self):
        """Return the temperature."""
        return self.coordinator.data["Temperature"][self._unit_system]["Value"]

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS if self.coordinator.is_metric else TEMP_FAHRENHEIT

    @property
    def pressure(self):
        """Return the pressure."""
        return self.coordinator.data["Pressure"][self._unit_system]["Value"]

    @property
    def humidity(self):
        """Return the humidity."""
        return self.coordinator.data["RelativeHumidity"]

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self.coordinator.data["Wind"]["Speed"][self._unit_system]["Value"]

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self.coordinator.data["Wind"]["Direction"]["Degrees"]

    @property
    def visibility(self):
        """Return the visibility."""
        return self.coordinator.data["Visibility"][self._unit_system]["Value"]

    @property
    def ozone(self):
        """Return the ozone level."""
        # We only have ozone data for certain locations and only in the forecast data.
        if self.coordinator.forecast and self.coordinator.data[ATTR_FORECAST][0].get(
            "Ozone"
        ):
            return self.coordinator.data[ATTR_FORECAST][0]["Ozone"]["Value"]
        return None

    @property
    def forecast(self):
        """Return the forecast array."""
        if not self.coordinator.forecast:
            return None
        # remap keys from library to keys understood by the weather component
        forecast = [
            {
                ATTR_FORECAST_TIME: utc_from_timestamp(item["EpochDate"]).isoformat(),
                ATTR_FORECAST_TEMP: item["TemperatureMax"]["Value"],
                ATTR_FORECAST_TEMP_LOW: item["TemperatureMin"]["Value"],
                ATTR_FORECAST_PRECIPITATION: self._calc_precipitation(item),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: round(
                    mean(
                        [
                            item["PrecipitationProbabilityDay"],
                            item["PrecipitationProbabilityNight"],
                        ]
                    )
                ),
                ATTR_FORECAST_WIND_SPEED: item["WindDay"]["Speed"]["Value"],
                ATTR_FORECAST_WIND_BEARING: item["WindDay"]["Direction"]["Degrees"],
                ATTR_FORECAST_CONDITION: [
                    k for k, v in CONDITION_CLASSES.items() if item["IconDay"] in v
                ][0],
            }
            for item in self.coordinator.data[ATTR_FORECAST]
        ]
        return forecast

    @staticmethod
    def _calc_precipitation(day: dict) -> float:
        """Return sum of the precipitation."""
        precip_sum = 0
        precip_types = ["Rain", "Snow", "Ice"]
        for precip in precip_types:
            precip_sum = sum(
                [
                    precip_sum,
                    day[f"{precip}Day"]["Value"],
                    day[f"{precip}Night"]["Value"],
                ]
            )
        return round(precip_sum, 1)
