"""Binary sensor platform for Opp.io addons."""
from typing import Callable, List

from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity

from . import ADDONS_COORDINATOR
from .const import ATTR_UPDATE_AVAILABLE
from .entity import OppioAddonEntity, OppioOSEntity


async def async_setup_entry(
    opp: OpenPeerPower,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Binary sensor set up for Opp.io config entry."""
    coordinator = opp.data[ADDONS_COORDINATOR]

    entities = [
        OppioAddonBinarySensor(
            coordinator, addon, ATTR_UPDATE_AVAILABLE, "Update Available"
        )
        for addon in coordinator.data["addons"].values()
    ]
    if coordinator.is_opp_os:
        entities.append(
            OppioOSBinarySensor(coordinator, ATTR_UPDATE_AVAILABLE, "Update Available")
        )
    async_add_entities(entities)


class OppioAddonBinarySensor(OppioAddonEntity, BinarySensorEntity):
    """Binary sensor to track whether an update is available for a Opp.io add-on."""

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.addon_info[self.attribute_name]


class OppioOSBinarySensor(OppioOSEntity, BinarySensorEntity):
    """Binary sensor to track whether an update is available for Opp.io OS."""

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.os_info[self.attribute_name]
