"""The BSB-Lan integration."""
from datetime import timedelta

from bsblan import BSBLan, BSBLanConnectionError

from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_PASSKEY, DATA_BSBLAN_CLIENT, DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)

PLATFORMS = [CLIMATE_DOMAIN]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up BSB-Lan from a config entry."""

    session = async_get_clientsession(opp)
    bsblan = BSBLan(
        entry.data[CONF_HOST],
        passkey=entry.data[CONF_PASSKEY],
        port=entry.data[CONF_PORT],
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
        session=session,
    )

    try:
        await bsblan.info()
    except BSBLanConnectionError as exception:
        raise ConfigEntryNotReady from exception

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {DATA_BSBLAN_CLIENT: bsblan}

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload BSBLan config entry."""

    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Cleanup
        del opp.data[DOMAIN][entry.entry_id]
        if not opp.data[DOMAIN]:
            del opp.data[DOMAIN]

    return unload_ok
