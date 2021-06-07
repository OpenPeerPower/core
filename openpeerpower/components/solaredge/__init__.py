"""The SolarEdge integration."""
from __future__ import annotations

from requests.exceptions import ConnectTimeout, HTTPError
from solaredge import Solaredge

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_API_KEY
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv

from .const import CONF_SITE_ID, DATA_API_CLIENT, DOMAIN, LOGGER

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

PLATFORMS = ["sensor"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up SolarEdge from a config entry."""
    api = Solaredge(entry.data[CONF_API_KEY])

    try:
        response = await opp.async_add_executor_job(
            api.get_details, entry.data[CONF_SITE_ID]
        )
    except (ConnectTimeout, HTTPError) as ex:
        LOGGER.error("Could not retrieve details from SolarEdge API")
        raise ConfigEntryNotReady from ex

    if "details" not in response:
        LOGGER.error("Missing details data in SolarEdge response")
        raise ConfigEntryNotReady

    if response["details"].get("status", "").lower() != "active":
        LOGGER.error("SolarEdge site is not active")
        return False

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_API_CLIENT: api}
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload SolarEdge config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del opp.data[DOMAIN][entry.entry_id]
    return unload_ok
