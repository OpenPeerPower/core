"""Roon (www.roonlabs.com) component."""
from openpeerpower.const import CONF_HOST
from openpeerpower.helpers import device_registry as dr

from .const import DOMAIN
from .server import RoonServer


async def async_setup(opp, config):
    """Set up the Roon platform."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp, entry):
    """Set up a roonserver from a config entry."""
    host = entry.data[CONF_HOST]
    roonserver = RoonServer(opp, entry)

    if not await roonserver.async_setup():
        return False

    opp.data[DOMAIN][entry.entry_id] = roonserver
    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Roonlabs",
        name=host,
    )
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    roonserver = opp.data[DOMAIN].pop(entry.entry_id)
    return await roonserver.async_reset()
