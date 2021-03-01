"""BleBox switch implementation."""
from openpeerpower.components.switch import SwitchEntity

from . import BleBoxEntity, create_blebox_entities
from .const import BLEBOX_TO_OPP_DEVICE_CLASSES


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up a BleBox switch entity."""
    create_blebox_entities(
        opp, config_entry, async_add_entities, BleBoxSwitchEntity, "switches"
    )


class BleBoxSwitchEntity(BleBoxEntity, SwitchEntity):
    """Representation of a BleBox switch feature."""

    @property
    def device_class(self):
        """Return the device class."""
        return BLEBOX_TO_OPP_DEVICE_CLASSES[self._feature.device_class]

    @property
    def is_on(self):
        """Return whether switch is on."""
        return self._feature.is_on

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        await self._feature.async_turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self._feature.async_turn_off()
