"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence

from pysmartthings import Attribute, Capability

from openpeerpower.components.switch import SwitchEntity

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Add switches for a config entry."""
    broker = opp.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    async_add_entities(
        [
            SmartThingsSwitch(device)
            for device in broker.devices.values()
            if broker.any_assigned(device.device_id, "switch")
        ]
    )


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must be able to be turned on/off.
    if Capability.switch in capabilities:
        return [Capability.switch, Capability.energy_meter, Capability.power_meter]
    return None


class SmartThingsSwitch(SmartThingsEntity, SwitchEntity):
    """Define a SmartThings switch."""

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._device.switch_off(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_op_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._device.switch_on(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_op_state()

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return self._device.status.attributes[Attribute.power].value

    @property
    def today_energy_kwh(self):
        """Return the today total energy usage in kWh."""
        return self._device.status.attributes[Attribute.energy].value

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._device.status.switch
