"""Base entity class for Flo entities."""

from typing import Any, Dict

from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC
from openpeerpower.helpers.entity import Entity

from .const import DOMAIN as FLO_DOMAIN
from .device import FloDeviceDataUpdateCoordinator


class FloEntity(Entity):
    """A base class for Flo entities."""

    def __init__(
        self,
        entity_type: str,
        name: str,
        device: FloDeviceDataUpdateCoordinator,
        **kwargs,
    ):
        """Init Flo entity."""
        self._unique_id: str = f"{device.mac_address}_{entity_type}"
        self._name: str = name
        self._device: FloDeviceDataUpdateCoordinator = device
        self._state: Any = None

    @property
    def name(self) -> str:
        """Return Entity's default name."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a device description for device registry."""
        return {
            "identifiers": {(FLO_DOMAIN, self._device.id)},
            "connections": {(CONNECTION_NETWORK_MAC, self._device.mac_address)},
            "manufacturer": self._device.manufacturer,
            "model": self._device.model,
            "name": self._device.device_name,
            "sw_version": self._device.firmware_version,
        }

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._device.available

    @property
    def force_update(self) -> bool:
        """Force update this entity."""
        return False

    @property
    def should_poll(self) -> bool:
        """Poll state from device."""
        return False

    async def async_update(self):
        """Update Flo entity."""
        await self._device.async_request_refresh()

    async def async_added_to_opp(self):
        """When entity is added to opp."""
        self.async_on_remove(self._device.async_add_listener(self.async_write_op_state))
