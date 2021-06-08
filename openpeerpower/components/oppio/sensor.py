"""Sensor platform for Opp.io addons."""
from __future__ import annotations

from openpeerpower.components.sensor import SensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback

from . import ADDONS_COORDINATOR
from .const import ATTR_VERSION, ATTR_VERSION_LATEST
from .entity import OppioAddonEntity, OppioOSEntity


async def async_setup_entry(
    opp: OpenPeerPower,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor set up for Opp.io config entry."""
    coordinator = opp.data[ADDONS_COORDINATOR]

    entities = []

    for attribute_name, sensor_name in (
        (ATTR_VERSION, "Version"),
        (ATTR_VERSION_LATEST, "Newest Version"),
    ):
        for addon in coordinator.data["addons"].values():
            entities.append(
                OppioAddonSensor(coordinator, addon, attribute_name, sensor_name)
            )
        if coordinator.is_opp_os:
            entities.append(OppioOSSensor(coordinator, attribute_name, sensor_name))

    async_add_entities(entities)


class OppioAddonSensor(OppioAddonEntity, SensorEntity):
    """Sensor to track a Opp.io add-on attribute."""

    @property
    def state(self) -> str:
        """Return state of entity."""
        return self.addon_info[self.attribute_name]


class OppioOSSensor(OppioOSEntity, SensorEntity):
    """Sensor to track a Opp.io add-on attribute."""

    @property
    def state(self) -> str:
        """Return state of entity."""
        return self.os_info[self.attribute_name]
