"""The twinkly component."""

import twinkly_client

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import CONF_ENTRY_HOST, CONF_ENTRY_ID, DOMAIN


async def async_setup(opp: OpenPeerPowerType, config: dict):
    """Set up the twinkly integration."""

    return True


async def async_setup_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry):
    """Set up entries from config flow."""

    # We setup the client here so if at some point we add any other entity for this device,
    # we will be able to properly share the connection.
    uuid = config_entry.data[CONF_ENTRY_ID]
    host = config_entry.data[CONF_ENTRY_HOST]

    opp.data.setdefault(DOMAIN, {})[uuid] = twinkly_client.TwinklyClient(
        host, async_get_clientsession(opp)
    )

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, "light")
    )
    return True


async def async_unload_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry):
    """Remove a twinkly entry."""

    # For now light entries don't have unload method, so we don't have to async_forward_entry_unload
    # However we still have to cleanup the shared client!
    uuid = config_entry.data[CONF_ENTRY_ID]
    opp.data[DOMAIN].pop(uuid)

    return True
