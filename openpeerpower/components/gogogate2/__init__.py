"""The gogogate2 component."""
import asyncio

from openpeerpower.components.cover import DOMAIN as COVER
from openpeerpower.components.sensor import DOMAIN as SENSOR
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_DEVICE
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .common import get_data_update_coordinator
from .const import DEVICE_TYPE_GOGOGATE2

PLATFORMS = [COVER, SENSOR]


async def async_setup(opp: OpenPeerPower, base_config: dict) -> bool:
    """Set up for Gogogate2 controllers."""
    return True


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Do setup of Gogogate2."""

    # Update the config entry.
    config_updates = {}
    if CONF_DEVICE not in config_entry.data:
        config_updates["data"] = {
            **config_entry.data,
            **{CONF_DEVICE: DEVICE_TYPE_GOGOGATE2},
        }

    if config_updates:
        opp.config_entries.async_update_entry(config_entry, **config_updates)

    data_update_coordinator = get_data_update_coordinator(opp, config_entry)
    await data_update_coordinator.async_refresh()

    if not data_update_coordinator.last_update_success:
        raise ConfigEntryNotReady()

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Unload Gogogate2 config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    return unload_ok
