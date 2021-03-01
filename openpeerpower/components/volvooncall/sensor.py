"""Support for Volvo On Call sensors."""
from . import DATA_KEY, VolvoEntity


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Volvo sensors."""
    if discovery_info is None:
        return
    async_add_entities([VolvoSensor(opp.data[DATA_KEY], *discovery_info)])


class VolvoSensor(VolvoEntity):
    """Representation of a Volvo sensor."""

    @property
    def state(self):
        """Return the state."""
        return self.instrument.state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.instrument.unit
