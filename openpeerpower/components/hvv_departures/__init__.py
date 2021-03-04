"""The HVV integration."""
import asyncio

from openpeerpower.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from openpeerpower.components.sensor import DOMAIN as DOMAIN_SENSOR
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import aiohttp_client

from .const import DOMAIN
from .hub import GTIHub

PLATFORMS = [DOMAIN_SENSOR, DOMAIN_BINARY_SENSOR]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the HVV component."""
    return True


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

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    return unload_ok
