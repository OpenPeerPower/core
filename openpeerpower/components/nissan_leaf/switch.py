"""Charge and Climate Control Support for the Nissan Leaf."""
import logging

from openpeerpower.helpers.entity import ToggleEntity

from . import DATA_CLIMATE, DATA_LEAF, LeafEntity

_LOGGER = logging.getLogger(__name__)


def setup_platform(opp, config, add_devices, discovery_info=None):
    """Nissan Leaf switch platform setup."""
    if discovery_info is None:
        return

    devices = []
    for vin, datastore in opp.data[DATA_LEAF].items():
        _LOGGER.debug("Adding switch for vin=%s", vin)
        devices.append(LeafClimateSwitch(datastore))

    add_devices(devices, True)


class LeafClimateSwitch(LeafEntity, ToggleEntity):
    """Nissan Leaf Climate Control switch."""

    @property
    def name(self):
        """Switch name."""
        return f"{self.car.leaf.nickname} Climate Control"

    def log_registration(self):
        """Log registration."""
        _LOGGER.debug(
            "Registered LeafClimateSwitch integration with Open Peer Power for VIN %s",
            self.car.leaf.vin,
        )

    @property
    def extra_state_attributes(self):
        """Return climate control attributes."""
        attrs = super().extra_state_attributes
        attrs["updated_on"] = self.car.last_climate_response
        return attrs

    @property
    def is_on(self):
        """Return true if climate control is on."""
        return self.car.data[DATA_CLIMATE]

    async def async_turn_on(self, **kwargs):
        """Turn on climate control."""
        if await self.car.async_set_climate(True):
            self.car.data[DATA_CLIMATE] = True

    async def async_turn_off(self, **kwargs):
        """Turn off climate control."""
        if await self.car.async_set_climate(False):
            self.car.data[DATA_CLIMATE] = False
