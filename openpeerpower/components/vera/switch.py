"""Support for Vera switches."""
from typing import Any, Callable, List, Optional

import pyvera as veraApi

from openpeerpower.components.switch import (
    DOMAIN as PLATFORM_DOMAIN,
    ENTITY_ID_FORMAT,
    SwitchEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity
from openpeerpower.util import convert

from . import VeraDevice
from .common import ControllerData, get_controller_data


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up the sensor config entry."""
    controller_data = get_controller_data(opp, entry)
    async_add_entities(
        [
            VeraSwitch(device, controller_data)
            for device in controller_data.devices.get(PLATFORM_DOMAIN)
        ],
        True,
    )


class VeraSwitch(VeraDevice[veraApi.VeraSwitch], SwitchEntity):
    """Representation of a Vera Switch."""

    def __init__(
        self, vera_device: veraApi.VeraSwitch, controller_data: ControllerData
    ):
        """Initialize the Vera device."""
        self._state = False
        VeraDevice.__init__(self, vera_device, controller_data)
        self.entity_id = ENTITY_ID_FORMAT.format(self.vera_id)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        self.vera_device.switch_on()
        self._state = True
        self.schedule_update_op_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        self.vera_device.switch_off()
        self._state = False
        self.schedule_update_op_state()

    @property
    def current_power_w(self) -> Optional[float]:
        """Return the current power usage in W."""
        power = self.vera_device.power
        if power:
            return convert(power, float, 0.0)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._state

    def update(self) -> None:
        """Update device state."""
        super().update()
        self._state = self.vera_device.is_switched_on()
