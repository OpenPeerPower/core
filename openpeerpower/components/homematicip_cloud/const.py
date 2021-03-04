"""Constants for the HomematicIP Cloud component."""
import logging

from openpeerpower.components.alarm_control_panel import (
    DOMAIN as ALARM_CONTROL_PANEL_DOMAIN,
)
from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.cover import DOMAIN as COVER_DOMAIN
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.components.weather import DOMAIN as WEATHER_DOMAIN

_LOGGER = logging.getLogger(".")

DOMAIN = "homematicip_cloud"

PLATFORMS = [
    ALARM_CONTROL_PANEL_DOMAIN,
    BINARY_SENSOR_DOMAIN,
    CLIMATE_DOMAIN,
    COVER_DOMAIN,
    LIGHT_DOMAIN,
    SENSOR_DOMAIN,
    SWITCH_DOMAIN,
    WEATHER_DOMAIN,
]

CONF_ACCESSPOINT = "accesspoint"
CONF_AUTHTOKEN = "authtoken"

HMIPC_NAME = "name"
HMIPC_HAPID = "hapid"
HMIPC_AUTHTOKEN = "authtoken"
HMIPC_PIN = "pin"
