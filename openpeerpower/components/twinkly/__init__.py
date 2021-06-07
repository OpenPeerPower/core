"""The twinkly component."""

import twinkly_client

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_ENTRY_HOST, CONF_ENTRY_ID, DOMAIN

PLATFORMS = ["light"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up entries from config flow."""

    # We setup the client here so if at some point we add any other entity for this device,
    # we will be able to properly share the connection.
    uuid = entry.data[CONF_ENTRY_ID]
    host = entry.data[CONF_ENTRY_HOST]

    opp.data.setdefault(DOMAIN, {})[uuid] = twinkly_client.TwinklyClient(
        host, async_get_clientsession(opp)
    )

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Remove a twinkly entry."""

    # For now light entries don't have unload method, so we don't have to async_forward_entry_unload
    # However we still have to cleanup the shared client!
    uuid = entry.data[CONF_ENTRY_ID]
    opp.data[DOMAIN].pop(uuid)

    return True
