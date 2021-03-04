"""Support for deCONZ switches."""
from openpeerpower.components.fan import (
    DOMAIN,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import FANS, NEW_LIGHT
from .deconz_device import DeconzDevice
from .gateway import get_gateway_from_config_entry

SPEEDS = {SPEED_OFF: 0, SPEED_LOW: 1, SPEED_MEDIUM: 2, SPEED_HIGH: 4}
SUPPORTED_ON_SPEEDS = {1: SPEED_LOW, 2: SPEED_MEDIUM, 4: SPEED_HIGH}


def convert_speed(speed: int) -> str:
    """Convert speed from deCONZ to OPP.

    Fallback to medium speed if unsupported by OPP fan platform.
    """
    if speed in SPEEDS.values():
        for opp_speed, deconz_speed in SPEEDS.items():
            if speed == deconz_speed:
                return opp_speed
    return SPEED_MEDIUM


async def async_setup_entry(opp, config_entry, async_add_entities) -> None:
    """Set up fans for deCONZ component."""
    gateway = get_gateway_from_config_entry(opp, config_entry)
    gateway.entities[DOMAIN] = set()

    @callback
    def async_add_fan(lights=gateway.api.lights.values()) -> None:
        """Add fan from deCONZ."""
        entities = []

        for light in lights:

            if light.type in FANS and light.uniqueid not in gateway.entities[DOMAIN]:
                entities.append(DeconzFan(light, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(
            opp, gateway.async_signal_new_device(NEW_LIGHT), async_add_fan
        )
    )

    async_add_fan()


class DeconzFan(DeconzDevice, FanEntity):
    """Representation of a deCONZ fan."""

    TYPE = DOMAIN

    def __init__(self, device, gateway) -> None:
        """Set up fan."""
        super().__init__(device, gateway)

        self._default_on_speed = SPEEDS[SPEED_MEDIUM]
        if self.speed != SPEED_OFF:
            self._default_on_speed = self._device.speed

        self._features = SUPPORT_SET_SPEED

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        return self.speed != SPEED_OFF

    @property
    def speed(self) -> int:
        """Return the current speed."""
        return convert_speed(self._device.speed)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return list(SPEEDS)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._features

    @callback
    def async_update_callback(self, force_update=False) -> None:
        """Store latest configured speed from the device."""
        if self.speed != SPEED_OFF and self._device.speed != self._default_on_speed:
            self._default_on_speed = self._device.speed
        super().async_update_callback(force_update)

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if speed not in SPEEDS:
            raise ValueError(f"Unsupported speed {speed}")

        await self._device.set_speed(SPEEDS[speed])

    #
    # The fan entity model has changed to use percentages and preset_modes
    # instead of speeds.
    #
    # Please review
    # https://developers.openpeerpower.io/docs/core/entity/fan/
    #
    async def async_turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Turn on fan."""
        if not speed:
            speed = convert_speed(self._default_on_speed)
        await self.async_set_speed(speed)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off fan."""
        await self.async_set_speed(SPEED_OFF)
