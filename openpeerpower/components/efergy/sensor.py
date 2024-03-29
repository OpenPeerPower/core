"""Support for Efergy sensors."""
import logging

import requests
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA, SensorEntity
from openpeerpower.const import (
    CONF_CURRENCY,
    CONF_MONITORED_VARIABLES,
    CONF_TYPE,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
)
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
_RESOURCE = "https://engage.efergy.com/mobile_proxy/"

CONF_APPTOKEN = "app_token"
CONF_UTC_OFFSET = "utc_offset"

CONF_PERIOD = "period"

CONF_INSTANT = "instant_readings"
CONF_AMOUNT = "amount"
CONF_BUDGET = "budget"
CONF_COST = "cost"
CONF_CURRENT_VALUES = "current_values"

DEFAULT_PERIOD = "year"
DEFAULT_UTC_OFFSET = "0"

SENSOR_TYPES = {
    CONF_INSTANT: ["Energy Usage", POWER_WATT],
    CONF_AMOUNT: ["Energy Consumed", ENERGY_KILO_WATT_HOUR],
    CONF_BUDGET: ["Energy Budget", None],
    CONF_COST: ["Energy Cost", None],
    CONF_CURRENT_VALUES: ["Per-Device Usage", POWER_WATT],
}

TYPES_SCHEMA = vol.In(SENSOR_TYPES)

SENSORS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TYPE): TYPES_SCHEMA,
        vol.Optional(CONF_CURRENCY, default=""): cv.string,
        vol.Optional(CONF_PERIOD, default=DEFAULT_PERIOD): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_APPTOKEN): cv.string,
        vol.Optional(CONF_UTC_OFFSET, default=DEFAULT_UTC_OFFSET): cv.string,
        vol.Required(CONF_MONITORED_VARIABLES): [SENSORS_SCHEMA],
    }
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the Efergy sensor."""
    app_token = config.get(CONF_APPTOKEN)
    utc_offset = str(config.get(CONF_UTC_OFFSET))

    dev = []
    for variable in config[CONF_MONITORED_VARIABLES]:
        if variable[CONF_TYPE] == CONF_CURRENT_VALUES:
            url_string = f"{_RESOURCE}getCurrentValuesSummary?token={app_token}"
            response = requests.get(url_string, timeout=10)
            for sensor in response.json():
                sid = sensor["sid"]
                dev.append(
                    EfergySensor(
                        variable[CONF_TYPE],
                        app_token,
                        utc_offset,
                        variable[CONF_PERIOD],
                        variable[CONF_CURRENCY],
                        sid,
                    )
                )
        dev.append(
            EfergySensor(
                variable[CONF_TYPE],
                app_token,
                utc_offset,
                variable[CONF_PERIOD],
                variable[CONF_CURRENCY],
            )
        )

    add_entities(dev, True)


class EfergySensor(SensorEntity):
    """Implementation of an Efergy sensor."""

    def __init__(self, sensor_type, app_token, utc_offset, period, currency, sid=None):
        """Initialize the sensor."""
        self.sid = sid
        if sid:
            self._name = f"efergy_{sid}"
        else:
            self._name = SENSOR_TYPES[sensor_type][0]
        self.type = sensor_type
        self.app_token = app_token
        self.utc_offset = utc_offset
        self._state = None
        self.period = period
        self.currency = currency
        if self.type == "cost":
            self._unit_of_measurement = f"{self.currency}/{self.period}"
        else:
            self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        """Get the Efergy monitor data from the web service."""
        try:
            if self.type == "instant_readings":
                url_string = f"{_RESOURCE}getInstant?token={self.app_token}"
                response = requests.get(url_string, timeout=10)
                self._state = response.json()["reading"]
            elif self.type == "amount":
                url_string = f"{_RESOURCE}getEnergy?token={self.app_token}&offset={self.utc_offset}&period={self.period}"
                response = requests.get(url_string, timeout=10)
                self._state = response.json()["sum"]
            elif self.type == "budget":
                url_string = f"{_RESOURCE}getBudget?token={self.app_token}"
                response = requests.get(url_string, timeout=10)
                self._state = response.json()["status"]
            elif self.type == "cost":
                url_string = f"{_RESOURCE}getCost?token={self.app_token}&offset={self.utc_offset}&period={self.period}"
                response = requests.get(url_string, timeout=10)
                self._state = response.json()["sum"]
            elif self.type == "current_values":
                url_string = (
                    f"{_RESOURCE}getCurrentValuesSummary?token={self.app_token}"
                )
                response = requests.get(url_string, timeout=10)
                for sensor in response.json():
                    if self.sid == sensor["sid"]:
                        measurement = next(iter(sensor["data"][0].values()))
                        self._state = measurement
            else:
                self._state = None
        except (requests.RequestException, ValueError, KeyError):
            _LOGGER.warning("Could not update status for %s", self.name)
