"""The gogogate2 component."""
from openpeerpower.components.cover import DOMAIN as COVER_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_DEVICE
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .common import get_data_update_coordinator
from .const import DEVICE_TYPE_GOGOGATE2


async def async_setup_opp: OpenPeerPower, base_config: dict) -> bool:
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

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, COVER_DOMAIN)
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Unload Gogogate2 config entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_unload(config_entry, COVER_DOMAIN)
    )

    return True
