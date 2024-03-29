"""The Broadlink integration."""
from __future__ import annotations

from dataclasses import dataclass, field

from .const import DOMAIN
from .device import BroadlinkDevice
from .heartbeat import BroadlinkHeartbeat


@dataclass
class BroadlinkData:
    """Class for sharing data within the Broadlink integration."""

    devices: dict = field(default_factory=dict)
    platforms: dict = field(default_factory=dict)
    heartbeat: BroadlinkHeartbeat | None = None


async def async_setup(opp, config):
    """Set up the Broadlink integration."""
    opp.data[DOMAIN] = BroadlinkData()
    return True


async def async_setup_entry(opp, entry):
    """Set up a Broadlink device from a config entry."""
    data = opp.data[DOMAIN]

    if data.heartbeat is None:
        data.heartbeat = BroadlinkHeartbeat(opp)
        opp.async_create_task(data.heartbeat.async_setup())

    device = BroadlinkDevice(opp, entry)
    return await device.async_setup()


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    data = opp.data[DOMAIN]

    device = data.devices.pop(entry.entry_id)
    result = await device.async_unload()

    if not data.devices:
        await data.heartbeat.async_unload()
        data.heartbeat = None

    return result
