"""Light/LED support for the Skybell HD Doorbell."""
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
)
import openpeerpower.util.color as color_util

from . import DOMAIN as SKYBELL_DOMAIN, SkybellDevice


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up the platform for a Skybell device."""
    skybell = opp.data.get(SKYBELL_DOMAIN)

    sensors = []
    for device in skybell.get_devices():
        sensors.append(SkybellLight(device))

    add_entities(sensors, True)


def _to_skybell_level(level):
    """Convert the given Open Peer Power light level (0-255) to Skybell (0-100)."""
    return int((level * 100) / 255)


def _to_opp_level(level):
    """Convert the given Skybell (0-100) light level to Open Peer Power (0-255)."""
    return int((level * 255) / 100)


class SkybellLight(SkybellDevice, LightEntity):
    """A binary sensor implementation for Skybell devices."""

    def __init__(self, device):
        """Initialize a light for a Skybell device."""
        super().__init__(device)
        self._name = self._device.name

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def turn_on(self, **kwargs):
        """Turn on the light."""
        if ATTR_HS_COLOR in kwargs:
            rgb = color_util.color_hs_to_RGB(*kwargs[ATTR_HS_COLOR])
            self._device.led_rgb = rgb
        elif ATTR_BRIGHTNESS in kwargs:
            self._device.led_intensity = _to_skybell_level(kwargs[ATTR_BRIGHTNESS])
        else:
            self._device.led_intensity = _to_skybell_level(255)

    def turn_off(self, **kwargs):
        """Turn off the light."""
        self._device.led_intensity = 0

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._device.led_intensity > 0

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return _to_opp_level(self._device.led_intensity)

    @property
    def hs_color(self):
        """Return the color of the light."""
        return color_util.color_RGB_to_hs(*self._device.led_rgb)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR
