"""Support for Fritzbox binary sensors."""
from __future__ import annotations

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_WINDOW,
    BinarySensorEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback

from . import FritzBoxEntity
from .const import CONF_COORDINATOR, DOMAIN as FRITZBOX_DOMAIN


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the FRITZ!SmartHome binary sensor from ConfigEntry."""
    entities: list[FritzboxBinarySensor] = []
    coordinator = opp.data[FRITZBOX_DOMAIN][entry.entry_id][CONF_COORDINATOR]

    for ain, device in coordinator.data.items():
        if not device.has_alarm:
            continue

        entities.append(
            FritzboxBinarySensor(
                {
                    ATTR_NAME: f"{device.name}",
                    ATTR_ENTITY_ID: f"{device.ain}",
                    ATTR_UNIT_OF_MEASUREMENT: None,
                    ATTR_DEVICE_CLASS: DEVICE_CLASS_WINDOW,
                },
                coordinator,
                ain,
            )
        )

    async_add_entities(entities)


class FritzboxBinarySensor(FritzBoxEntity, BinarySensorEntity):
    """Representation of a binary FRITZ!SmartHome device."""

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""
        if not self.device.present:
            return False
        return self.device.alert_state  # type: ignore [no-any-return]
