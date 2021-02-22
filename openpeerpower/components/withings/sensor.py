"""Sensors flow for Withings."""
from typing import Callable, List, Union

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
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
        opp,
        entry,
        WithingsHealthSensor,
        SENSOR_DOMAIN,
    )

    async_add_entities(entities, True)


class WithingsHealthSensor(BaseWithingsSensor):
    """Implementation of a Withings sensor."""

    @property
    def state(self) -> Union[None, str, int, float]:
        """Return the state of the entity."""
        return self._state_data
