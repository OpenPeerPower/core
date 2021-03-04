"""Support for Bond lights."""
import logging
from typing import Any, Callable, List, Optional

from bond_api import Action, BPUPSubscriptions, DeviceType

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity

from . import BondHub
from .const import BPUP_SUBS, DOMAIN, HUB
from .entity import BondEntity
from .utils import BondDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    opp: OpenPeerPower,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up Bond light devices."""
    data = opp.data[DOMAIN][entry.entry_id]
    hub: BondHub = data[HUB]
    bpup_subs: BPUPSubscriptions = data[BPUP_SUBS]

    fan_lights: List[Entity] = [
        BondLight(hub, device, bpup_subs)
        for device in hub.devices
        if DeviceType.is_fan(device.type)
        and device.supports_light()
        and not (device.supports_up_light() and device.supports_down_light())
    ]

    fan_up_lights: List[Entity] = [
        BondUpLight(hub, device, bpup_subs, "up_light")
        for device in hub.devices
        if DeviceType.is_fan(device.type) and device.supports_up_light()
    ]

    fan_down_lights: List[Entity] = [
        BondDownLight(hub, device, bpup_subs, "down_light")
        for device in hub.devices
        if DeviceType.is_fan(device.type) and device.supports_down_light()
    ]

    fireplaces: List[Entity] = [
        BondFireplace(hub, device, bpup_subs)
        for device in hub.devices
        if DeviceType.is_fireplace(device.type)
    ]

    fp_lights: List[Entity] = [
        BondLight(hub, device, bpup_subs, "light")
        for device in hub.devices
        if DeviceType.is_fireplace(device.type) and device.supports_light()
    ]

    lights: List[Entity] = [
        BondLight(hub, device, bpup_subs)
        for device in hub.devices
        if DeviceType.is_light(device.type)
    ]

    async_add_entities(
        fan_lights + fan_up_lights + fan_down_lights + fireplaces + fp_lights + lights,
        True,
    )


class BondBaseLight(BondEntity, LightEntity):
    """Representation of a Bond light."""

    def __init__(
        self,
        hub: BondHub,
        device: BondDevice,
        bpup_subs: BPUPSubscriptions,
        sub_device: Optional[str] = None,
    ):
        """Create OP entity representing Bond light."""
        super().__init__(hub, device, bpup_subs, sub_device)
        self._light: Optional[int] = None

    @property
    def is_on(self) -> bool:
        """Return if light is currently on."""
        return self._light == 1

    @property
    def supported_features(self) -> Optional[int]:
        """Flag supported features."""
        return 0


class BondLight(BondBaseLight, BondEntity, LightEntity):
    """Representation of a Bond light."""

    def __init__(
        self,
        hub: BondHub,
        device: BondDevice,
        bpup_subs: BPUPSubscriptions,
        sub_device: Optional[str] = None,
    ):
        """Create OP entity representing Bond light."""
        super().__init__(hub, device, bpup_subs, sub_device)
        self._brightness: Optional[int] = None

    def _apply_state(self, state: dict) -> None:
        self._light = state.get("light")
        self._brightness = state.get("brightness")

    @property
    def supported_features(self) -> Optional[int]:
        """Flag supported features."""
        if self._device.supports_set_brightness():
            return SUPPORT_BRIGHTNESS
        return 0

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of this light between 1..255."""
        brightness_value = (
            round(self._brightness * 255 / 100) if self._brightness else None
        )
        return brightness_value

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness:
            await self._hub.bond.action(
                self._device.device_id,
                Action.set_brightness(round((brightness * 100) / 255)),
            )
        else:
            await self._hub.bond.action(self._device.device_id, Action.turn_light_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._hub.bond.action(self._device.device_id, Action.turn_light_off())


class BondDownLight(BondBaseLight, BondEntity, LightEntity):
    """Representation of a Bond light."""

    def _apply_state(self, state: dict) -> None:
        self._light = state.get("down_light") and state.get("light")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        await self._hub.bond.action(
            self._device.device_id, Action(Action.TURN_DOWN_LIGHT_ON)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._hub.bond.action(
            self._device.device_id, Action(Action.TURN_DOWN_LIGHT_OFF)
        )


class BondUpLight(BondBaseLight, BondEntity, LightEntity):
    """Representation of a Bond light."""

    def _apply_state(self, state: dict) -> None:
        self._light = state.get("up_light") and state.get("light")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        await self._hub.bond.action(
            self._device.device_id, Action(Action.TURN_UP_LIGHT_ON)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._hub.bond.action(
            self._device.device_id, Action(Action.TURN_UP_LIGHT_OFF)
        )


class BondFireplace(BondEntity, LightEntity):
    """Representation of a Bond-controlled fireplace."""

    def __init__(self, hub: BondHub, device: BondDevice, bpup_subs: BPUPSubscriptions):
        """Create OP entity representing Bond fireplace."""
        super().__init__(hub, device, bpup_subs)

        self._power: Optional[bool] = None
        # Bond flame level, 0-100
        self._flame: Optional[int] = None

    def _apply_state(self, state: dict) -> None:
        self._power = state.get("power")
        self._flame = state.get("flame")

    @property
    def supported_features(self) -> Optional[int]:
        """Flag brightness as supported feature to represent flame level."""
        return SUPPORT_BRIGHTNESS

    @property
    def is_on(self) -> bool:
        """Return True if power is on."""
        return self._power == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the fireplace on."""
        _LOGGER.debug("Fireplace async_turn_on called with: %s", kwargs)

        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness:
            flame = round((brightness * 100) / 255)
            await self._hub.bond.action(self._device.device_id, Action.set_flame(flame))
        else:
            await self._hub.bond.action(self._device.device_id, Action.turn_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fireplace off."""
        _LOGGER.debug("Fireplace async_turn_off called with: %s", kwargs)

        await self._hub.bond.action(self._device.device_id, Action.turn_off())

    @property
    def brightness(self) -> Optional[int]:
        """Return the flame of this fireplace converted to OP brightness between 0..255."""
        return round(self._flame * 255 / 100) if self._flame else None

    @property
    def icon(self) -> Optional[str]:
        """Show fireplace icon for the entity."""
        return "mdi:fireplace" if self._power == 1 else "mdi:fireplace-off"
