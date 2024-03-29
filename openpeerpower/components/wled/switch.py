"""Support for WLED switches."""
from __future__ import annotations

from typing import Any

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback

from . import WLEDDataUpdateCoordinator, WLEDEntity, wled_exception_handler
from .const import (
    ATTR_DURATION,
    ATTR_FADE,
    ATTR_TARGET_BRIGHTNESS,
    ATTR_UDP_PORT,
    DOMAIN,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WLED switch based on a config entry."""
    coordinator: WLEDDataUpdateCoordinator = opp.data[DOMAIN][entry.entry_id]

    switches = [
        WLEDNightlightSwitch(coordinator),
        WLEDSyncSendSwitch(coordinator),
        WLEDSyncReceiveSwitch(coordinator),
    ]
    async_add_entities(switches, True)


class WLEDNightlightSwitch(WLEDEntity, SwitchEntity):
    """Defines a WLED nightlight switch."""

    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator: WLEDDataUpdateCoordinator) -> None:
        """Initialize WLED nightlight switch."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.data.info.name} Nightlight"
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_nightlight"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {
            ATTR_DURATION: self.coordinator.data.state.nightlight.duration,
            ATTR_FADE: self.coordinator.data.state.nightlight.fade,
            ATTR_TARGET_BRIGHTNESS: self.coordinator.data.state.nightlight.target_brightness,
        }

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return bool(self.coordinator.data.state.nightlight.on)

    @wled_exception_handler
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the WLED nightlight switch."""
        await self.coordinator.wled.nightlight(on=False)

    @wled_exception_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the WLED nightlight switch."""
        await self.coordinator.wled.nightlight(on=True)


class WLEDSyncSendSwitch(WLEDEntity, SwitchEntity):
    """Defines a WLED sync send switch."""

    _attr_icon = "mdi:upload-network-outline"

    def __init__(self, coordinator: WLEDDataUpdateCoordinator) -> None:
        """Initialize WLED sync send switch."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.data.info.name} Sync Send"
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_sync_send"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {ATTR_UDP_PORT: self.coordinator.data.info.udp_port}

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return bool(self.coordinator.data.state.sync.send)

    @wled_exception_handler
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the WLED sync send switch."""
        await self.coordinator.wled.sync(send=False)

    @wled_exception_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the WLED sync send switch."""
        await self.coordinator.wled.sync(send=True)


class WLEDSyncReceiveSwitch(WLEDEntity, SwitchEntity):
    """Defines a WLED sync receive switch."""

    _attr_icon = "mdi:download-network-outline"

    def __init__(self, coordinator: WLEDDataUpdateCoordinator) -> None:
        """Initialize WLED sync receive switch."""
        super().__init__(coordinator=coordinator)
        self._attr_name = f"{coordinator.data.info.name} Sync Receive"
        self._attr_unique_id = f"{coordinator.data.info.mac_address}_sync_receive"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the entity."""
        return {ATTR_UDP_PORT: self.coordinator.data.info.udp_port}

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return bool(self.coordinator.data.state.sync.receive)

    @wled_exception_handler
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the WLED sync receive switch."""
        await self.coordinator.wled.sync(receive=False)

    @wled_exception_handler
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the WLED sync receive switch."""
        await self.coordinator.wled.sync(receive=True)
