"""Support for Vera lights."""
from typing import Any, Callable, List, Optional, Tuple

import pyvera as veraApi

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    DOMAIN as PLATFORM_DOMAIN,
    ENTITY_ID_FORMAT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity import Entity
import openpeerpower.util.color as color_util

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
            VeraLight(device, controller_data)
            for device in controller_data.devices.get(PLATFORM_DOMAIN)
        ],
        True,
    )


class VeraLight(VeraDevice[veraApi.VeraDimmer], LightEntity):
    """Representation of a Vera Light, including dimmable."""

    def __init__(
        self, vera_device: veraApi.VeraDimmer, controller_data: ControllerData
    ):
        """Initialize the light."""
        self._state = False
        self._color = None
        self._brightness = None
        VeraDevice.__init__(self, vera_device, controller_data)
        self.entity_id = ENTITY_ID_FORMAT.format(self.vera_id)

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self) -> Optional[Tuple[float, float]]:
        """Return the color of the light."""
        return self._color

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        if self._color:
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        return SUPPORT_BRIGHTNESS

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if ATTR_HS_COLOR in kwargs and self._color:
            rgb = color_util.color_hs_to_RGB(*kwargs[ATTR_HS_COLOR])
            self.vera_device.set_color(rgb)
        elif ATTR_BRIGHTNESS in kwargs and self.vera_device.is_dimmable:
            self.vera_device.set_brightness(kwargs[ATTR_BRIGHTNESS])
        else:
            self.vera_device.switch_on()

        self._state = True
        self.schedule_update_op_state(True)

    def turn_off(self, **kwargs: Any):
        """Turn the light off."""
        self.vera_device.switch_off()
        self._state = False
        self.schedule_update_op_state()

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._state

    def update(self) -> None:
        """Call to update state."""
        super().update()
        self._state = self.vera_device.is_switched_on()
        if self.vera_device.is_dimmable:
            # If it is dimmable, both functions exist. In case color
            # is not supported, it will return None
            self._brightness = self.vera_device.get_brightness()
            rgb = self.vera_device.get_color()
            self._color = color_util.color_RGB_to_hs(*rgb) if rgb else None
