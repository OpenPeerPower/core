"""The HVV integration."""

from openpeerpower.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from openpeerpower.components.sensor import DOMAIN as DOMAIN_SENSOR
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import aiohttp_client

from .const import DOMAIN
from .hub import GTIHub

PLATFORMS = [DOMAIN_SENSOR, DOMAIN_BINARY_SENSOR]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up HVV from a config entry."""

    hub = GTIHub(
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        aiohttp_client.async_get_clientsession(opp),
    )

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = hub

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
