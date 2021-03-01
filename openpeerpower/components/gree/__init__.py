"""The Gree Climate integration."""
import asyncio
import logging

from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .bridge import CannotConnect, DeviceDataUpdateCoordinator, DeviceHelper
from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Gree Climate component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Gree Climate from a config entry."""
    devices = []

    # First we'll grab as many devices as we can find on the network
    # it's necessary to bind static devices anyway
    _LOGGER.debug("Scanning network for Gree devices")

    for device_info in await DeviceHelper.find_devices():
        try:
            device = await DeviceHelper.try_bind_device(device_info)
        except CannotConnect:
            _LOGGER.error("Unable to bind to gree device: %s", device_info)
            continue

        _LOGGER.debug(
            "Adding Gree device at %s:%i (%s)",
            device.device_info.ip,
            device.device_info.port,
            device.device_info.name,
        )
        devices.append(device)

    coordinators = [DeviceDataUpdateCoordinator(opp, d) for d in devices]
    await asyncio.gather(*[x.async_refresh() for x in coordinators])

    opp.data[DOMAIN][COORDINATOR] = coordinators
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, CLIMATE_DOMAIN)
    )
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, SWITCH_DOMAIN)
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    results = asyncio.gather(
        opp.config_entries.async_forward_entry_unload(entry, CLIMATE_DOMAIN),
        opp.config_entries.async_forward_entry_unload(entry, SWITCH_DOMAIN),
    )

    unload_ok = all(await results)
    if unload_ok:
        opp.data[DOMAIN].pop("devices", None)
        opp.data[DOMAIN].pop(CLIMATE_DOMAIN, None)
        opp.data[DOMAIN].pop(SWITCH_DOMAIN, None)

    return unload_ok
