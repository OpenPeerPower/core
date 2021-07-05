"""Support for Elgato Lights."""
import logging

from elgato import Elgato, ElgatoConnectionError

from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import DATA_ELGATO_CLIENT, DOMAIN

PLATFORMS = [LIGHT_DOMAIN]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Elgato Light from a config entry."""
    session = async_get_clientsession(opp)
    elgato = Elgato(
        entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        session=session,
    )

    # Ensure we can connect to it
    try:
        await elgato.info()
    except ElgatoConnectionError as exception:
        logging.getLogger(__name__).debug("Unable to connect: %s", exception)
        raise ConfigEntryNotReady from exception

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {DATA_ELGATO_CLIENT: elgato}
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Elgato Light config entry."""
    # Unload entities for this entry/device.
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Cleanup
        del opp.data[DOMAIN][entry.entry_id]
        if not opp.data[DOMAIN]:
            del opp.data[DOMAIN]
    return unload_ok
