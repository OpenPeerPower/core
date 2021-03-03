"""The Broadlink integration."""
from dataclasses import dataclass, field

from .const import DOMAIN
from .device import BroadlinkDevice


@dataclass
class BroadlinkData:
    """Class for sharing data within the Broadlink integration."""

    devices: dict = field(default_factory=dict)
    platforms: dict = field(default_factory=dict)


async def async_setup(opp, config):
    """Set up the Broadlink integration."""
    opp.data[DOMAIN] = BroadlinkData()
    return True


async def async_setup_entry(opp, entry):
    """Set up a Broadlink device from a config entry."""
    device = BroadlinkDevice(opp, entry)
    return await device.async_setup()


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    device = opp.data[DOMAIN].devices.pop(entry.entry_id)
    return await device.async_unload()
