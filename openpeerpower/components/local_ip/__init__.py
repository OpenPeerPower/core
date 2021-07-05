"""Get the local IP address of the Open Peer Power instance."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN, PLATFORMS

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up local_ip from a config entry."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
