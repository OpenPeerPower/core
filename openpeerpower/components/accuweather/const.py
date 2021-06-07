"""Constants for AccuWeather integration."""
from __future__ import annotations

from typing import Final

from openpeerpower.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    CONCENTRATION_PARTS_PER_CUBIC_METER,
    DEVICE_CLASS_TEMPERATURE,
    LENGTH_FEET,
    LENGTH_INCHES,
    LENGTH_METERS,
    LENGTH_MILLIMETERS,
    PERCENTAGE,
    SPEED_KILOMETERS_PER_HOUR,
    SPEED_MILES_PER_HOUR,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TIME_HOURS,
    UV_INDEX,
)

from .model import SensorDescription

API_IMPERIAL: Final = "Imperial"
API_METRIC: Final = "Metric"
ATTRIBUTION: Final = "Data provided by AccuWeather"
ATTR_ENABLED: Final = "enabled"
ATTR_FORECAST: Final = "forecast"
ATTR_LABEL: Final = "label"
ATTR_UNIT_IMPERIAL: Final = "unit_imperial"
ATTR_UNIT_METRIC: Final = "unit_metric"
CONF_FORECAST: Final = "forecast"
COORDINATOR: Final = "coordinator"
DOMAIN: Final = "accuweather"
MANUFACTURER: Final = "AccuWeather, Inc."
MAX_FORECAST_DAYS: Final = 4
NAME: Final = "AccuWeather"
UNDO_UPDATE_LISTENER: Final = "undo_update_listener"

CONDITION_CLASSES: Final[dict[str, list[int]]] = {
    ATTR_CONDITION_CLEAR_NIGHT: [33, 34, 37],
    ATTR_CONDITION_CLOUDY: [7, 8, 38],
    ATTR_CONDITION_EXCEPTIONAL: [24, 30, 31],
    ATTR_CONDITION_FOG: [11],
    ATTR_CONDITION_HAIL: [25],
    ATTR_CONDITION_LIGHTNING: [15],
    ATTR_CONDITION_LIGHTNING_RAINY: [16, 17, 41, 42],
    ATTR_CONDITION_PARTLYCLOUDY: [3, 4, 6, 35, 36],
    ATTR_CONDITION_POURING: [18],
    ATTR_CONDITION_RAINY: [12, 13, 14, 26, 39, 40],
    ATTR_CONDITION_SNOWY: [19, 20, 21, 22, 23, 43, 44],
    ATTR_CONDITION_SNOWY_RAINY: [29],
    ATTR_CONDITION_SUNNY: [1, 2, 5],
    ATTR_CONDITION_WINDY: [32],
}

FORECAST_SENSOR_TYPES: Final[dict[str, SensorDescription]] = {
    "CloudCoverDay": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-cloudy",
        ATTR_LABEL: "Cloud Cover Day",
        ATTR_UNIT_METRIC: PERCENTAGE,
        ATTR_UNIT_IMPERIAL: PERCENTAGE,
        ATTR_ENABLED: False,
    },
    "CloudCoverNight": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-cloudy",
        ATTR_LABEL: "Cloud Cover Night",
        ATTR_UNIT_METRIC: PERCENTAGE,
        ATTR_UNIT_IMPERIAL: PERCENTAGE,
        ATTR_ENABLED: False,
    },
    "Grass": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:grass",
        ATTR_LABEL: "Grass Pollen",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_ENABLED: False,
    },
    "HoursOfSun": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-partly-cloudy",
        ATTR_LABEL: "Hours Of Sun",
        ATTR_UNIT_METRIC: TIME_HOURS,
        ATTR_UNIT_IMPERIAL: TIME_HOURS,
        ATTR_ENABLED: True,
    },
    "Mold": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: "Mold Pollen",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_ENABLED: False,
    },
    "Ozone": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:vector-triangle",
        ATTR_LABEL: "Ozone",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
        ATTR_ENABLED: False,
    },
    "Ragweed": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:sprout",
        ATTR_LABEL: "Ragweed Pollen",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_ENABLED: False,
    },
    "RealFeelTemperatureMax": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "RealFeel Temperature Max",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: True,
    },
    "RealFeelTemperatureMin": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "RealFeel Temperature Min",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: True,
    },
    "RealFeelTemperatureShadeMax": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "RealFeel Temperature Shade Max",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "RealFeelTemperatureShadeMin": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "RealFeel Temperature Shade Min",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "ThunderstormProbabilityDay": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-lightning",
        ATTR_LABEL: "Thunderstorm Probability Day",
        ATTR_UNIT_METRIC: PERCENTAGE,
        ATTR_UNIT_IMPERIAL: PERCENTAGE,
        ATTR_ENABLED: True,
    },
    "ThunderstormProbabilityNight": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-lightning",
        ATTR_LABEL: "Thunderstorm Probability Night",
        ATTR_UNIT_METRIC: PERCENTAGE,
        ATTR_UNIT_IMPERIAL: PERCENTAGE,
        ATTR_ENABLED: True,
    },
    "Tree": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:tree-outline",
        ATTR_LABEL: "Tree Pollen",
        ATTR_UNIT_METRIC: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_UNIT_IMPERIAL: CONCENTRATION_PARTS_PER_CUBIC_METER,
        ATTR_ENABLED: False,
    },
    "UVIndex": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-sunny",
        ATTR_LABEL: "UV Index",
        ATTR_UNIT_METRIC: UV_INDEX,
        ATTR_UNIT_IMPERIAL: UV_INDEX,
        ATTR_ENABLED: True,
    },
    "WindGustDay": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "Wind Gust Day",
        ATTR_UNIT_METRIC: SPEED_KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: SPEED_MILES_PER_HOUR,
        ATTR_ENABLED: False,
    },
    "WindGustNight": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "Wind Gust Night",
        ATTR_UNIT_METRIC: SPEED_KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: SPEED_MILES_PER_HOUR,
        ATTR_ENABLED: False,
    },
    "WindDay": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "Wind Day",
        ATTR_UNIT_METRIC: SPEED_KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: SPEED_MILES_PER_HOUR,
        ATTR_ENABLED: True,
    },
    "WindNight": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "Wind Night",
        ATTR_UNIT_METRIC: SPEED_KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: SPEED_MILES_PER_HOUR,
        ATTR_ENABLED: True,
    },
}

SENSOR_TYPES: Final[dict[str, SensorDescription]] = {
    "ApparentTemperature": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "Apparent Temperature",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "Ceiling": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-fog",
        ATTR_LABEL: "Cloud Ceiling",
        ATTR_UNIT_METRIC: LENGTH_METERS,
        ATTR_UNIT_IMPERIAL: LENGTH_FEET,
        ATTR_ENABLED: True,
    },
    "CloudCover": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-cloudy",
        ATTR_LABEL: "Cloud Cover",
        ATTR_UNIT_METRIC: PERCENTAGE,
        ATTR_UNIT_IMPERIAL: PERCENTAGE,
        ATTR_ENABLED: False,
    },
    "DewPoint": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "Dew Point",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "RealFeelTemperature": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "RealFeel Temperature",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: True,
    },
    "RealFeelTemperatureShade": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "RealFeel Temperature Shade",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "Precipitation": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-rainy",
        ATTR_LABEL: "Precipitation",
        ATTR_UNIT_METRIC: LENGTH_MILLIMETERS,
        ATTR_UNIT_IMPERIAL: LENGTH_INCHES,
        ATTR_ENABLED: True,
    },
    "PressureTendency": {
        ATTR_DEVICE_CLASS: "accuweather__pressure_tendency",
        ATTR_ICON: "mdi:gauge",
        ATTR_LABEL: "Pressure Tendency",
        ATTR_UNIT_METRIC: None,
        ATTR_UNIT_IMPERIAL: None,
        ATTR_ENABLED: True,
    },
    "UVIndex": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-sunny",
        ATTR_LABEL: "UV Index",
        ATTR_UNIT_METRIC: UV_INDEX,
        ATTR_UNIT_IMPERIAL: UV_INDEX,
        ATTR_ENABLED: True,
    },
    "WetBulbTemperature": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "Wet Bulb Temperature",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "WindChillTemperature": {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_ICON: None,
        ATTR_LABEL: "Wind Chill Temperature",
        ATTR_UNIT_METRIC: TEMP_CELSIUS,
        ATTR_UNIT_IMPERIAL: TEMP_FAHRENHEIT,
        ATTR_ENABLED: False,
    },
    "Wind": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "Wind",
        ATTR_UNIT_METRIC: SPEED_KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: SPEED_MILES_PER_HOUR,
        ATTR_ENABLED: True,
    },
    "WindGust": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
        ATTR_LABEL: "Wind Gust",
        ATTR_UNIT_METRIC: SPEED_KILOMETERS_PER_HOUR,
        ATTR_UNIT_IMPERIAL: SPEED_MILES_PER_HOUR,
        ATTR_ENABLED: False,
    },
}
