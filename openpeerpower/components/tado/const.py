"""Constant values for the Tado component."""

from PyTado.const import (
    CONST_HVAC_COOL,
    CONST_HVAC_DRY,
    CONST_HVAC_FAN,
    CONST_HVAC_HEAT,
    CONST_HVAC_HOT_WATER,
    CONST_HVAC_IDLE,
    CONST_HVAC_OFF,
)

from openpeerpower.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_FAN,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_HOME,
)

TADO_HVAC_ACTION_TO_HA_HVAC_ACTION = {
    CONST_HVAC_HEAT: CURRENT_HVAC_HEAT,
    CONST_HVAC_DRY: CURRENT_HVAC_DRY,
    CONST_HVAC_FAN: CURRENT_HVAC_FAN,
    CONST_HVAC_COOL: CURRENT_HVAC_COOL,
    CONST_HVAC_IDLE: CURRENT_HVAC_IDLE,
    CONST_HVAC_OFF: CURRENT_HVAC_OFF,
    CONST_HVAC_HOT_WATER: CURRENT_HVAC_HEAT,
}

# Configuration
CONF_FALLBACK = "fallback"
DATA = "data"
UPDATE_TRACK = "update_track"

# Weather
CONDITIONS_MAP = {
    "clear-night": {"NIGHT_CLEAR"},
    "cloudy": {"CLOUDY", "CLOUDY_MOSTLY", "NIGHT_CLOUDY"},
    "fog": {"FOGGY"},
    "hail": {"HAIL", "RAIN_HAIL"},
    "lightning": {"THUNDERSTORM"},
    "partlycloudy": {"CLOUDY_PARTLY"},
    "rainy": {"DRIZZLE", "RAIN", "SCATTERED_RAIN"},
    "snowy": {"FREEZING", "SCATTERED_SNOW", "SNOW"},
    "snowy-rainy": {"RAIN_SNOW", "SCATTERED_RAIN_SNOW"},
    "sunny": {"SUN"},
    "windy": {"WIND"},
}

# Types
TYPE_AIR_CONDITIONING = "AIR_CONDITIONING"
TYPE_HEATING = "HEATING"
TYPE_HOT_WATER = "HOT_WATER"

TYPE_BATTERY = "BATTERY"
TYPE_POWER = "POWER"

# Base modes
CONST_MODE_OFF = "OFF"
CONST_MODE_SMART_SCHEDULE = "SMART_SCHEDULE"  # Use the schedule
CONST_MODE_AUTO = "AUTO"
CONST_MODE_COOL = "COOL"
CONST_MODE_HEAT = "HEAT"
CONST_MODE_DRY = "DRY"
CONST_MODE_FAN = "FAN"

CONST_LINK_OFFLINE = "OFFLINE"

CONST_FAN_OFF = "OFF"
CONST_FAN_AUTO = "AUTO"
CONST_FAN_LOW = "LOW"
CONST_FAN_MIDDLE = "MIDDLE"
CONST_FAN_HIGH = "HIGH"


# When we change the temperature setting, we need an overlay mode
CONST_OVERLAY_TADO_MODE = (
    "NEXT_TIME_BLOCK"  # wait until tado changes the mode automatic
)
CONST_OVERLAY_MANUAL = "MANUAL"  # the user has change the temperature or mode manually
CONST_OVERLAY_TIMER = "TIMER"  # the temperature will be reset after a timespan


# Heat always comes first since we get the
# min and max tempatures for the zone from
# it.
# Heat is preferred as it generally has a lower minimum temperature
ORDERED_KNOWN_TADO_MODES = [
    CONST_MODE_HEAT,
    CONST_MODE_COOL,
    CONST_MODE_AUTO,
    CONST_MODE_DRY,
    CONST_MODE_FAN,
]

TADO_MODES_TO_HA_CURRENT_HVAC_ACTION = {
    CONST_MODE_HEAT: CURRENT_HVAC_HEAT,
    CONST_MODE_DRY: CURRENT_HVAC_DRY,
    CONST_MODE_FAN: CURRENT_HVAC_FAN,
    CONST_MODE_COOL: CURRENT_HVAC_COOL,
}

# These modes will not allow a temp to be set
TADO_MODES_WITH_NO_TEMP_SETTING = [CONST_MODE_AUTO, CONST_MODE_DRY, CONST_MODE_FAN]
#
# HVAC_MODE_HEAT_COOL is mapped to CONST_MODE_AUTO
#    This lets tado decide on a temp
#
# HVAC_MODE_AUTO is mapped to CONST_MODE_SMART_SCHEDULE
#    This runs the smart schedule
#
HA_TO_TADO_HVAC_MODE_MAP = {
    HVAC_MODE_OFF: CONST_MODE_OFF,
    HVAC_MODE_HEAT_COOL: CONST_MODE_AUTO,
    HVAC_MODE_AUTO: CONST_MODE_SMART_SCHEDULE,
    HVAC_MODE_HEAT: CONST_MODE_HEAT,
    HVAC_MODE_COOL: CONST_MODE_COOL,
    HVAC_MODE_DRY: CONST_MODE_DRY,
    HVAC_MODE_FAN_ONLY: CONST_MODE_FAN,
}

HA_TO_TADO_FAN_MODE_MAP = {
    FAN_AUTO: CONST_FAN_AUTO,
    FAN_OFF: CONST_FAN_OFF,
    FAN_LOW: CONST_FAN_LOW,
    FAN_MEDIUM: CONST_FAN_MIDDLE,
    FAN_HIGH: CONST_FAN_HIGH,
}

TADO_TO_HA_HVAC_MODE_MAP = {
    value: key for key, value in HA_TO_TADO_HVAC_MODE_MAP.items()
}

TADO_TO_HA_FAN_MODE_MAP = {value: key for key, value in HA_TO_TADO_FAN_MODE_MAP.items()}

DEFAULT_TADO_PRECISION = 0.1

SUPPORT_PRESET = [PRESET_AWAY, PRESET_HOME]


TADO_SWING_OFF = "OFF"
TADO_SWING_ON = "ON"

DOMAIN = "tado"

SIGNAL_TADO_UPDATE_RECEIVED = "tado_update_received_{}_{}_{}"
UNIQUE_ID = "unique_id"

DEFAULT_NAME = "Tado"

TADO_HOME = "Home"
TADO_ZONE = "Zone"

UPDATE_LISTENER = "update_listener"

# Constants for Temperature Offset
INSIDE_TEMPERATURE_MEASUREMENT = "INSIDE_TEMPERATURE_MEASUREMENT"
TEMP_OFFSET = "temperatureOffset"
TADO_OFFSET_CELSIUS = "celsius"
HA_OFFSET_CELSIUS = "offset_celsius"
TADO_OFFSET_FAHRENHEIT = "fahrenheit"
HA_OFFSET_FAHRENHEIT = "offset_fahrenheit"
TADO_TO_HA_OFFSET_MAP = {
    TADO_OFFSET_CELSIUS: HA_OFFSET_CELSIUS,
    TADO_OFFSET_FAHRENHEIT: HA_OFFSET_FAHRENHEIT,
}
