"""Support for Velbus Binary Sensors."""
from openpeerpower.components.binary_sensor import BinarySensorEntity

from . import VelbusEntity
from .const import DOMAIN


async def async_setup_entry(opp, entry, async_add_entities):
    """Set up Velbus binary sensor based on config_entry."""
    cntrl = opp.data[DOMAIN][entry.entry_id]["cntrl"]
    modules_data = opp.data[DOMAIN][entry.entry_id]["binary_sensor"]
    entities = []
    for address, channel in modules_data:
        module = cntrl.get_module(address)
        entities.append(VelbusBinarySensor(module, channel))
    async_add_entities(entities)


class VelbusBinarySensor(VelbusEntity, BinarySensorEntity):
    """Representation of a Velbus Binary Sensor."""

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self._module.is_closed(self._channel)
