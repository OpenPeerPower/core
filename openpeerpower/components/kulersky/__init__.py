"""Kuler Sky lights integration."""

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DATA_ADDRESSES, DATA_DISCOVERY_SUBSCRIPTION, DOMAIN

PLATFORMS = ["light"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Kuler Sky from a config entry."""
    if DOMAIN not in opp.data:
        opp.data[DOMAIN] = {}
    if DATA_ADDRESSES not in opp.data[DOMAIN]:
        opp.data[DOMAIN][DATA_ADDRESSES] = set()

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    # Stop discovery
    unregister_discovery = opp.data[DOMAIN].pop(DATA_DISCOVERY_SUBSCRIPTION, None)
    if unregister_discovery:
        unregister_discovery()

    opp.data.pop(DOMAIN, None)

    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
