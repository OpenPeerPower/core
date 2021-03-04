"""Constants for the deCONZ component."""
import logging

from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.cover import DOMAIN as COVER_DOMAIN
from openpeerpower.components.fan import DOMAIN as FAN_DOMAIN
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.components.lock import DOMAIN as LOCK_DOMAIN
from openpeerpower.components.scene import DOMAIN as SCENE_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN

LOGGER = logging.getLogger(__package__)

DOMAIN = "deconz"

CONF_BRIDGE_ID = "bridgeid"
CONF_GROUP_ID_BASE = "group_id_base"

DEFAULT_PORT = 80
DEFAULT_ALLOW_CLIP_SENSOR = False
DEFAULT_ALLOW_DECONZ_GROUPS = True
DEFAULT_ALLOW_NEW_DEVICES = True

CONF_ALLOW_CLIP_SENSOR = "allow_clip_sensor"
CONF_ALLOW_DECONZ_GROUPS = "allow_deconz_groups"
CONF_ALLOW_NEW_DEVICES = "allow_new_devices"
CONF_MASTER_GATEWAY = "master"

PLATFORMS = [
    BINARY_SENSOR_DOMAIN,
    CLIMATE_DOMAIN,
    COVER_DOMAIN,
    FAN_DOMAIN,
    LIGHT_DOMAIN,
    LOCK_DOMAIN,
    SCENE_DOMAIN,
    SENSOR_DOMAIN,
    SWITCH_DOMAIN,
]

NEW_GROUP = "groups"
NEW_LIGHT = "lights"
NEW_SCENE = "scenes"
NEW_SENSOR = "sensors"

ATTR_DARK = "dark"
ATTR_LOCKED = "locked"
ATTR_OFFSET = "offset"
ATTR_ON = "on"
ATTR_VALVE = "valve"

# Covers
DAMPERS = ["Level controllable output"]
WINDOW_COVERS = ["Window covering device", "Window covering controller"]
COVER_TYPES = DAMPERS + WINDOW_COVERS

# Fans
FANS = ["Fan"]

# Locks
LOCKS = ["Door Lock"]
LOCK_TYPES = LOCKS

# Switches
POWER_PLUGS = ["On/Off light", "On/Off plug-in unit", "Smart plug"]
SIRENS = ["Warning device"]
SWITCH_TYPES = POWER_PLUGS + SIRENS

CONF_ANGLE = "angle"
CONF_GESTURE = "gesture"
CONF_XY = "xy"
