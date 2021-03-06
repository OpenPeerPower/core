"""Support for Qwikswitch relays."""
from openpeerpower.components.switch import SwitchEntity

from . import DOMAIN as QWIKSWITCH, QSToggleEntity


async def async_setup_platform(opp, _, add_entities, discovery_info=None):
    """Add switches from the main Qwikswitch component."""
    if discovery_info is None:
        return

    qsusb = opp.data[QWIKSWITCH]
    devs = [QSSwitch(qsid, qsusb) for qsid in discovery_info[QWIKSWITCH]]
    add_entities(devs)


class QSSwitch(QSToggleEntity, SwitchEntity):
    """Switch based on a Qwikswitch relay module."""
