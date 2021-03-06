"""Sensors flow for Withings."""
from typing import Callable, List

from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_OCCUPANCY,
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity

from .common import BaseWithingsSensor, async_create_entities


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up the sensor config entry."""
    entities = await async_create_entities(
        opp, entry, WithingsHealthBinarySensor, BINARY_SENSOR_DOMAIN
    )

    async_add_entities(entities, True)


class WithingsHealthBinarySensor(BaseWithingsSensor, BinarySensorEntity):
    """Implementation of a Withings sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._state_data

    @property
    def device_class(self) -> str:
        """Provide the device class."""
        return DEVICE_CLASS_OCCUPANCY
