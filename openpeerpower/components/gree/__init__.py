"""The Gree Climate integration."""
from datetime import timedelta
import logging

from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.event import async_track_time_interval

from .bridge import DiscoveryService
from .const import (
    COORDINATORS,
    DATA_DISCOVERY_INTERVAL,
    DATA_DISCOVERY_SERVICE,
    DISCOVERY_SCAN_INTERVAL,
    DISPATCHERS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [CLIMATE_DOMAIN, SWITCH_DOMAIN]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Gree Climate from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    gree_discovery = DiscoveryService(opp)
    opp.data[DATA_DISCOVERY_SERVICE] = gree_discovery

    opp.data[DOMAIN].setdefault(DISPATCHERS, [])
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def _async_scan_update(_=None):
        await gree_discovery.discovery.scan()

    _LOGGER.debug("Scanning network for Gree devices")
    await _async_scan_update()

    opp.data[DOMAIN][DATA_DISCOVERY_INTERVAL] = async_track_time_interval(
        opp, _async_scan_update, timedelta(seconds=DISCOVERY_SCAN_INTERVAL)
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    if opp.data[DOMAIN].get(DISPATCHERS) is not None:
        for cleanup in opp.data[DOMAIN][DISPATCHERS]:
            cleanup()

    if opp.data[DOMAIN].get(DATA_DISCOVERY_INTERVAL) is not None:
        opp.data[DOMAIN].pop(DATA_DISCOVERY_INTERVAL)()

    if opp.data.get(DATA_DISCOVERY_SERVICE) is not None:
        opp.data.pop(DATA_DISCOVERY_SERVICE)

    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        opp.data[DOMAIN].pop(COORDINATORS, None)
        opp.data[DOMAIN].pop(DISPATCHERS, None)

    return unload_ok
