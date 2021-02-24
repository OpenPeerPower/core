"""Support for Vera locks."""
from typing import Any, Callable, Dict, List, Optional

import pyvera as veraApi

from openpeerpower.components.lock import (
    DOMAIN as PLATFORM_DOMAIN,
    ENTITY_ID_FORMAT,
    LockEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import STATE_LOCKED, STATE_UNLOCKED
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity

from . import VeraDevice
from .common import ControllerData, get_controller_data

ATTR_LAST_USER_NAME = "changed_by_name"
ATTR_LOW_BATTERY = "low_battery"


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up the sensor config entry."""
    controller_data = get_controller_data(opp, entry)
    async_add_entities(
        [
            VeraLock(device, controller_data)
            for device in controller_data.devices.get(PLATFORM_DOMAIN)
        ],
        True,
    )


class VeraLock(VeraDevice[veraApi.VeraLock], LockEntity):
    """Representation of a Vera lock."""

    def __init__(self, vera_device: veraApi.VeraLock, controller_data: ControllerData):
        """Initialize the Vera device."""
        self._state = None
        VeraDevice.__init__(self, vera_device, controller_data)
        self.entity_id = ENTITY_ID_FORMAT.format(self.vera_id)

    def lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        self.vera_device.lock()
        self._state = STATE_LOCKED

    def unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        self.vera_device.unlock()
        self._state = STATE_UNLOCKED

    @property
    def is_locked(self) -> Optional[bool]:
        """Return true if device is on."""
        return self._state == STATE_LOCKED

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Who unlocked the lock and did a low battery alert fire.

        Reports on the previous poll cycle.
        changed_by_name is a string like 'Bob'.
        low_battery is 1 if an alert fired, 0 otherwise.
        """
        data = super().device_state_attributes

        last_user = self.vera_device.get_last_user_alert()
        if last_user is not None:
            data[ATTR_LAST_USER_NAME] = last_user[1]

        data[ATTR_LOW_BATTERY] = self.vera_device.get_low_battery_alert()
        return data

    @property
    def changed_by(self) -> Optional[str]:
        """Who unlocked the lock.

        Reports on the previous poll cycle.
        changed_by is an integer user ID.
        """
        last_user = self.vera_device.get_last_user_alert()
        if last_user is not None:
            return last_user[0]
        return None

    def update(self) -> None:
        """Update state by the Vera device callback."""
        self._state = (
            STATE_LOCKED if self.vera_device.is_locked(True) else STATE_UNLOCKED
        )
