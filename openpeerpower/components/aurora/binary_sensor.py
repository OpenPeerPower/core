"""Support for Aurora Forecast binary sensor."""
from openpeerpower.components.binary_sensor import BinarySensorEntity

from . import AuroraEntity
from .const import COORDINATOR, DOMAIN


async def async_setup_entry(opp, entry, async_add_entries):
    """Set up the binary_sensor platform."""
    coordinator = opp.data[DOMAIN][entry.entry_id][COORDINATOR]
    name = f"{coordinator.name} Aurora Visibility Alert"

    entity = AuroraSensor(coordinator=coordinator, name=name, icon="mdi:hazard-lights")

    async_add_entries([entity])


class AuroraSensor(AuroraEntity, BinarySensorEntity):
    """Implementation of an aurora sensor."""

    @property
    def is_on(self):
        """Return true if aurora is visible."""
        return self.coordinator.data > self.coordinator.threshold
