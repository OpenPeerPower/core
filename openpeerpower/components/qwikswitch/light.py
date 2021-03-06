"""Support for Qwikswitch Relays and Dimmers."""
from openpeerpower.components.light import SUPPORT_BRIGHTNESS, LightEntity

from . import DOMAIN as QWIKSWITCH, QSToggleEntity


async def async_setup_platform(opp, _, add_entities, discovery_info=None):
    """Add lights from the main Qwikswitch component."""
    if discovery_info is None:
        return

    qsusb = opp.data[QWIKSWITCH]
    devs = [QSLight(qsid, qsusb) for qsid in discovery_info[QWIKSWITCH]]
    add_entities(devs)


class QSLight(QSToggleEntity, LightEntity):
    """Light based on a Qwikswitch relay/dimmer module."""

    @property
    def brightness(self):
        """Return the brightness of this light (0-255)."""
        return self.device.value if self.device.is_dimmer else None

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS if self.device.is_dimmer else 0
