"""Component to interface with switches that can be controlled remotely."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, cast, final

import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)
from openpeerpower.helpers.entity import ToggleEntity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import bind_opp

# mypy: allow-untyped-defs, no-check-untyped-defs

DOMAIN = "switch"
SCAN_INTERVAL = timedelta(seconds=30)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

ATTR_TODAY_ENERGY_KWH = "today_energy_kwh"
ATTR_CURRENT_POWER_W = "current_power_w"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)

PROP_TO_ATTR = {
    "current_power_w": ATTR_CURRENT_POWER_W,
    "today_energy_kwh": ATTR_TODAY_ENERGY_KWH,
}

DEVICE_CLASS_OUTLET = "outlet"
DEVICE_CLASS_SWITCH = "switch"

DEVICE_CLASSES = [DEVICE_CLASS_OUTLET, DEVICE_CLASS_SWITCH]

DEVICE_CLASSES_SCHEMA = vol.All(vol.Lower, vol.In(DEVICE_CLASSES))

_LOGGER = logging.getLogger(__name__)


@bind_opp
def is_on(opp, entity_id):
    """Return if the switch is on based on the statemachine.

    Async friendly.
    """
    return opp.states.is_state(entity_id, STATE_ON)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Track states and offer events for switches."""
    component = opp.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, opp, SCAN_INTERVAL)
    await component.async_setup(config)

    component.async_register_entity_service(SERVICE_TURN_OFF, {}, "async_turn_off")
    component.async_register_entity_service(SERVICE_TURN_ON, {}, "async_turn_on")
    component.async_register_entity_service(SERVICE_TOGGLE, {}, "async_toggle")

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    return cast(bool, await opp.data[DOMAIN].async_setup_entry(entry))


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return cast(bool, await opp.data[DOMAIN].async_unload_entry(entry))


class SwitchEntity(ToggleEntity):
    """Base class for switch entities."""

    _attr_current_power_w: float | None = None
    _attr_today_energy_kwh: float | None = None

    @property
    def current_power_w(self) -> float | None:
        """Return the current power usage in W."""
        return self._attr_current_power_w

    @property
    def today_energy_kwh(self) -> float | None:
        """Return the today total energy usage in kWh."""
        return self._attr_today_energy_kwh

    @final
    @property
    def state_attributes(self) -> dict[str, Any] | None:
        """Return the optional state attributes."""
        data = {}

        for prop, attr in PROP_TO_ATTR.items():
            value = getattr(self, prop)
            if value is not None:
                data[attr] = value

        return data


class SwitchDevice(SwitchEntity):
    """Representation of a switch (for backwards compatibility)."""

    def __init_subclass__(cls, **kwargs):
        """Print deprecation warning."""
        super().__init_subclass__(**kwargs)
        _LOGGER.warning(
            "SwitchDevice is deprecated, modify %s to extend SwitchEntity",
            cls.__name__,
        )
