"""Support for Aqualink temperature sensors."""
from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_COLD,
    DOMAIN,
    BinarySensorEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import AqualinkEntity
from .const import DOMAIN as AQUALINK_DOMAIN

PARALLEL_UPDATES = 0


async def async_setup_entry(
    opp: OpenPeerPowerType, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up discovered binary sensors."""
    devs = []
    for dev in opp.data[AQUALINK_DOMAIN][DOMAIN]:
        devs.append(OppAqualinkBinarySensor(dev))
    async_add_entities(devs, True)


class OppAqualinkBinarySensor(AqualinkEntity, BinarySensorEntity):
    """Representation of a binary sensor."""

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return self.dev.label

    @property
    def is_on(self) -> bool:
        """Return whether the binary sensor is on or not."""
        return self.dev.is_on

    @property
    def device_class(self) -> str:
        """Return the class of the binary sensor."""
        if self.name == "Freeze Protection":
            return DEVICE_CLASS_COLD
        return None
