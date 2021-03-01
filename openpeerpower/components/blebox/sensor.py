"""BleBox sensor entities."""

from openpeerpower.helpers.entity import Entity

from . import BleBoxEntity, create_blebox_entities
from .const import BLEBOX_TO_OPP_DEVICE_CLASSES, BLEBOX_TO_UNIT_MAP


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up a BleBox entry."""

    create_blebox_entities(
        opp, config_entry, async_add_entities, BleBoxSensorEntity, "sensors"
    )


class BleBoxSensorEntity(BleBoxEntity, Entity):
    """Representation of a BleBox sensor feature."""

    @property
    def state(self):
        """Return the state."""
        return self._feature.current

    @property
    def unit_of_measurement(self):
        """Return the unit."""
        return BLEBOX_TO_UNIT_MAP[self._feature.unit]

    @property
    def device_class(self):
        """Return the device class."""
        return BLEBOX_TO_OPP_DEVICE_CLASSES[self._feature.device_class]
