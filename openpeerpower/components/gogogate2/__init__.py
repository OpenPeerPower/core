"""The gogogate2 component."""

from openpeerpower.components.cover import DOMAIN as COVER
from openpeerpower.components.sensor import DOMAIN as SENSOR
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_DEVICE
from openpeerpower.core import OpenPeerPower

from .common import get_data_update_coordinator
from .const import DEVICE_TYPE_GOGOGATE2

PLATFORMS = [COVER, SENSOR]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Do setup of Gogogate2."""

    # Update the config entry.
    config_updates = {}
    if CONF_DEVICE not in entry.data:
        config_updates["data"] = {
            **entry.data,
            **{CONF_DEVICE: DEVICE_TYPE_GOGOGATE2},
        }

    if config_updates:
        opp.config_entries.async_update_entry(entry, **config_updates)

    data_update_coordinator = get_data_update_coordinator(opp, entry)
    await data_update_coordinator.async_config_entry_first_refresh()

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Gogogate2 config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
