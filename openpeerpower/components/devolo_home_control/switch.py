"""Platform for switch integration."""
from openpeerpower.components.switch import SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import DOMAIN
from .devolo_device import DevoloDeviceEntity


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Get all devices and setup the switch devices via config entry."""
    entities = []

    for gateway in opp.data[DOMAIN][entry.entry_id]["gateways"]:
        for device in gateway.binary_switch_devices:
            for binary_switch in device.binary_switch_property:
                # Exclude the binary switch which also has multi_level_switches here,
                # because those are implemented as light entities now.
                if not hasattr(device, "multi_level_switch_property"):
                    entities.append(
                        DevoloSwitch(
                            homecontrol=gateway,
                            device_instance=device,
                            element_uid=binary_switch,
                        )
                    )

    async_add_entities(entities)


class DevoloSwitch(DevoloDeviceEntity, SwitchEntity):
    """Representation of a switch."""

    def __init__(self, homecontrol, device_instance, element_uid):
        """Initialize an devolo Switch."""
        super().__init__(
            homecontrol=homecontrol,
            device_instance=device_instance,
            element_uid=element_uid,
        )
        self._binary_switch_property = self._device_instance.binary_switch_property.get(
            self._unique_id
        )
        self._is_on = self._binary_switch_property.state

        if hasattr(self._device_instance, "consumption_property"):
            self._consumption = self._device_instance.consumption_property.get(
                self._unique_id.replace("BinarySwitch", "Meter")
            ).current
        else:
            self._consumption = None

    @property
    def is_on(self):
        """Return the state."""
        return self._is_on

    @property
    def current_power_w(self):
        """Return the current consumption."""
        return self._consumption

    def turn_on(self, **kwargs):
        """Switch on the device."""
        self._is_on = True
        self._binary_switch_property.set(state=True)

    def turn_off(self, **kwargs):
        """Switch off the device."""
        self._is_on = False
        self._binary_switch_property.set(state=False)

    def _sync(self, message):
        """Update the binary switch state and consumption."""
        if message[0].startswith("devolo.BinarySwitch"):
            self._is_on = self._device_instance.binary_switch_property[message[0]].state
        elif message[0].startswith("devolo.Meter"):
            self._consumption = self._device_instance.consumption_property[
                message[0]
            ].current
        else:
            self._generic_message(message)
        self.schedule_update_op_state()
