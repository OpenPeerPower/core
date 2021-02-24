"""Support for Axis lights."""

from axis.event_stream import CLASS_LIGHT

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .axis_base import AxisEventBase
from .const import DOMAIN as AXIS_DOMAIN


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up a Axis light."""
    device = opp.data[AXIS_DOMAIN][config_entry.unique_id]

    if (
        device.api.vapix.light_control is None
        or len(device.api.vapix.light_control) == 0
    ):
        return

    @callback
    def async_add_sensor(event_id):
        """Add light from Axis device."""
        event = device.api.event[event_id]

        if event.CLASS == CLASS_LIGHT and event.TYPE == "Light":
            async_add_entities([AxisLight(event, device)])

    device.listeners.append(
        async_dispatcher_connect(opp, device.signal_new_event, async_add_sensor)
    )


class AxisLight(AxisEventBase, LightEntity):
    """Representation of a light Axis event."""

    def __init__(self, event, device):
        """Initialize the Axis light."""
        super().__init__(event, device)

        self.light_id = f"led{self.event.id}"

        self.current_intensity = 0
        self.max_intensity = 0

        self._features = SUPPORT_BRIGHTNESS

    async def async_added_to_opp(self) -> None:
        """Subscribe lights events."""
        await super().async_added_to_opp()

        current_intensity = (
            await self.device.api.vapix.light_control.get_current_intensity(
                self.light_id
            )
        )
        self.current_intensity = current_intensity["data"]["intensity"]

        max_intensity = await self.device.api.vapix.light_control.get_valid_intensity(
            self.light_id
        )
        self.max_intensity = max_intensity["data"]["ranges"][0]["high"]

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._features

    @property
    def name(self):
        """Return the name of the light."""
        light_type = self.device.api.vapix.light_control[self.light_id].light_type
        return f"{self.device.name} {light_type} {self.event.TYPE} {self.event.id}"

    @property
    def is_on(self):
        """Return true if light is on."""
        return self.event.is_tripped

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return int((self.current_intensity / self.max_intensity) * 255)

    async def async_turn_on(self, **kwargs):
        """Turn on light."""
        if not self.is_on:
            await self.device.api.vapix.light_control.activate_light(self.light_id)

        if ATTR_BRIGHTNESS in kwargs:
            intensity = int((kwargs[ATTR_BRIGHTNESS] / 255) * self.max_intensity)
            await self.device.api.vapix.light_control.set_manual_intensity(
                self.light_id, intensity
            )

    async def async_turn_off(self, **kwargs):
        """Turn off light."""
        if self.is_on:
            await self.device.api.vapix.light_control.deactivate_light(self.light_id)

    async def async_update(self):
        """Update brightness."""
        current_intensity = (
            await self.device.api.vapix.light_control.get_current_intensity(
                self.light_id
            )
        )
        self.current_intensity = current_intensity["data"]["intensity"]

    @property
    def should_poll(self):
        """Brightness needs polling."""
        return True
