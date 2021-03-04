"""The Ruckus Unleashed integration."""
import asyncio

from pyruckus import Ruckus

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import device_registry
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import (
    API_AP,
    API_DEVICE_NAME,
    API_ID,
    API_MAC,
    API_MODEL,
    API_SYSTEM_OVERVIEW,
    API_VERSION,
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    PLATFORMS,
    UNDO_UPDATE_LISTENERS,
)
from .coordinator import RuckusUnleashedDataUpdateCoordinator


async def async_setup(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up the Ruckus Unleashed component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Ruckus Unleashed from a config entry."""
    try:
        ruckus = await opp.async_add_executor_job(
            Ruckus,
            entry.data[CONF_HOST],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
    except ConnectionError as error:
        raise ConfigEntryNotReady from error

    coordinator = RuckusUnleashedDataUpdateCoordinator(opp, ruckus=ruckus)

    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    system_info = await opp.async_add_executor_job(ruckus.system_info)

    registry = await device_registry.async_get_registry(opp)
    ap_info = await opp.async_add_executor_job(ruckus.ap_info)
    for device in ap_info[API_AP][API_ID].values():
        registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections={(CONNECTION_NETWORK_MAC, device[API_MAC])},
            identifiers={(CONNECTION_NETWORK_MAC, device[API_MAC])},
            manufacturer=MANUFACTURER,
            name=device[API_DEVICE_NAME],
            model=device[API_MODEL],
            sw_version=system_info[API_SYSTEM_OVERVIEW][API_VERSION],
        )

    opp.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENERS: [],
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        for listener in opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENERS]:
            listener()

        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
