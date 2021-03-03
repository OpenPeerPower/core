"""Support for Elgato Key Lights."""
from elgato import Elgato, ElgatoConnectionError

from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.typing import ConfigType

from .const import DATA_ELGATO_CLIENT, DOMAIN


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the Elgato Key Light components."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Elgato Key Light from a config entry."""
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
        raise ConfigEntryNotReady from exception

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {DATA_ELGATO_CLIENT: elgato}

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, LIGHT_DOMAIN)
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Elgato Key Light config entry."""
    # Unload entities for this entry/device.
    await opp.config_entries.async_forward_entry_unload(entry, LIGHT_DOMAIN)

    # Cleanup
    del opp.data[DOMAIN][entry.entry_id]
    if not opp.data[DOMAIN]:
        del opp.data[DOMAIN]

    return True
