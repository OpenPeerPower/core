"""Component to interface with binary sensors."""
from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import StateType

# mypy: allow-untyped-defs, no-check-untyped-defs

_LOGGER = logging.getLogger(__name__)

DOMAIN = "binary_sensor"
SCAN_INTERVAL = timedelta(seconds=30)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

# On means low, Off means normal
DEVICE_CLASS_BATTERY = "battery"

# On means charging, Off means not charging
DEVICE_CLASS_BATTERY_CHARGING = "battery_charging"

# On means cold, Off means normal
DEVICE_CLASS_COLD = "cold"

# On means connected, Off means disconnected
DEVICE_CLASS_CONNECTIVITY = "connectivity"

# On means open, Off means closed
DEVICE_CLASS_DOOR = "door"

# On means open, Off means closed
DEVICE_CLASS_GARAGE_DOOR = "garage_door"

# On means gas detected, Off means no gas (clear)
DEVICE_CLASS_GAS = "gas"

# On means hot, Off means normal
DEVICE_CLASS_HEAT = "heat"

# On means light detected, Off means no light
DEVICE_CLASS_LIGHT = "light"

# On means open (unlocked), Off means closed (locked)
DEVICE_CLASS_LOCK = "lock"

# On means wet, Off means dry
DEVICE_CLASS_MOISTURE = "moisture"

# On means motion detected, Off means no motion (clear)
DEVICE_CLASS_MOTION = "motion"

# On means moving, Off means not moving (stopped)
DEVICE_CLASS_MOVING = "moving"

# On means occupied, Off means not occupied (clear)
DEVICE_CLASS_OCCUPANCY = "occupancy"

# On means open, Off means closed
DEVICE_CLASS_OPENING = "opening"

# On means plugged in, Off means unplugged
DEVICE_CLASS_PLUG = "plug"

# On means power detected, Off means no power
DEVICE_CLASS_POWER = "power"

# On means home, Off means away
DEVICE_CLASS_PRESENCE = "presence"

# On means problem detected, Off means no problem (OK)
DEVICE_CLASS_PROBLEM = "problem"

# On means unsafe, Off means safe
DEVICE_CLASS_SAFETY = "safety"

# On means smoke detected, Off means no smoke (clear)
DEVICE_CLASS_SMOKE = "smoke"

# On means sound detected, Off means no sound (clear)
DEVICE_CLASS_SOUND = "sound"

# On means vibration detected, Off means no vibration
DEVICE_CLASS_VIBRATION = "vibration"

# On means open, Off means closed
DEVICE_CLASS_WINDOW = "window"

DEVICE_CLASSES = [
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_BATTERY_CHARGING,
    DEVICE_CLASS_COLD,
    DEVICE_CLASS_CONNECTIVITY,
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_GARAGE_DOOR,
    DEVICE_CLASS_GAS,
    DEVICE_CLASS_HEAT,
    DEVICE_CLASS_LIGHT,
    DEVICE_CLASS_LOCK,
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_MOVING,
    DEVICE_CLASS_OCCUPANCY,
    DEVICE_CLASS_OPENING,
    DEVICE_CLASS_PLUG,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_PRESENCE,
    DEVICE_CLASS_PROBLEM,
    DEVICE_CLASS_SAFETY,
    DEVICE_CLASS_SMOKE,
    DEVICE_CLASS_SOUND,
    DEVICE_CLASS_VIBRATION,
    DEVICE_CLASS_WINDOW,
]

DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.In(DEVICE_CLASSES))


async def async_setup(opp, config):
    """Track states and offer events for binary sensors."""
    component = opp.data[DOMAIN] = EntityComponent(
        logging.getLogger(__name__), DOMAIN, opp, SCAN_INTERVAL
    )

    await component.async_setup(config)
    return True


async def async_setup_entry(opp, entry):
    """Set up a config entry."""
    return await opp.data[DOMAIN].async_setup_entry(entry)


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.data[DOMAIN].async_unload_entry(entry)


class BinarySensorEntity(Entity):
    """Represent a binary sensor."""

    _attr_is_on: bool | None = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._attr_is_on

    @property
    def state(self) -> StateType:
        """Return the state of the binary sensor."""
        return STATE_ON if self.is_on else STATE_OFF


class BinarySensorDevice(BinarySensorEntity):
    """Represent a binary sensor (for backwards compatibility)."""

    def __init_subclass__(cls, **kwargs):
        """Print deprecation warning."""
        super().__init_subclass__(**kwargs)
        _LOGGER.warning(
            "BinarySensorDevice is deprecated, modify %s to extend BinarySensorEntity",
            cls.__name__,
        )
