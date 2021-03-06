"""Support for Volvo heater."""
from openpeerpower.helpers.entity import ToggleEntity

from . import DATA_KEY, VolvoEntity


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up a Volvo switch."""
    if discovery_info is None:
        return
    async_add_entities([VolvoSwitch(opp.data[DATA_KEY], *discovery_info)])


class VolvoSwitch(VolvoEntity, ToggleEntity):
    """Representation of a Volvo switch."""

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.instrument.state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.instrument.turn_on()
        self.async_write_op_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.instrument.turn_off()
        self.async_write_op_state()
