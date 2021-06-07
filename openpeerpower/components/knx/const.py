"""Constants for the KNX integration."""
from enum import Enum
from typing import Final

from openpeerpower.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    PRESET_SLEEP,
)

DOMAIN: Final = "knx"

# Address is used for configuration and services by the same functions so the key has to match
KNX_ADDRESS: Final = "address"

CONF_KNX_ROUTING: Final = "routing"
CONF_KNX_TUNNELING: Final = "tunneling"
CONF_KNX_INDIVIDUAL_ADDRESS: Final = "individual_address"
CONF_INVERT: Final = "invert"
CONF_KNX_EXPOSE: Final = "expose"
CONF_STATE_ADDRESS: Final = "state_address"
CONF_SYNC_STATE: Final = "sync_state"
CONF_RESET_AFTER: Final = "reset_after"

ATTR_COUNTER: Final = "counter"
ATTR_SOURCE: Final = "source"
ATTR_LAST_KNX_UPDATE: Final = "last_knx_update"


class ColorTempModes(Enum):
    """Color temperature modes for config validation."""

    ABSOLUTE = "DPT-7.600"
    RELATIVE = "DPT-5.001"


class SupportedPlatforms(Enum):
    """Supported platforms."""

    BINARY_SENSOR = "binary_sensor"
    CLIMATE = "climate"
    COVER = "cover"
    FAN = "fan"
    LIGHT = "light"
    NOTIFY = "notify"
    SCENE = "scene"
    SENSOR = "sensor"
    SWITCH = "switch"
    WEATHER = "weather"


# Map KNX controller modes to OPP modes. This list might not be complete.
CONTROLLER_MODES: Final = {
    # Map DPT 20.105 HVAC control modes
    "Auto": HVAC_MODE_AUTO,
    "Heat": HVAC_MODE_HEAT,
    "Cool": HVAC_MODE_COOL,
    "Off": HVAC_MODE_OFF,
    "Fan only": HVAC_MODE_FAN_ONLY,
    "Dry": HVAC_MODE_DRY,
}

PRESET_MODES: Final = {
    # Map DPT 20.102 HVAC operating modes to OPP presets
    "Auto": PRESET_NONE,
    "Frost Protection": PRESET_ECO,
    "Night": PRESET_SLEEP,
    "Standby": PRESET_AWAY,
    "Comfort": PRESET_COMFORT,
}
