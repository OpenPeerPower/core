"""Support for SmartHab device integration."""
import logging

import pysmarthab
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv

DOMAIN = "smarthab"
DATA_HUB = "hub"
PLATFORMS = ["light", "cover"]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {
                    vol.Required(CONF_EMAIL): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config) -> bool:
    """Set up the SmartHab platform."""

    opp.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    if not opp.config_entries.async_entries(DOMAIN):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up config entry for SmartHab integration."""

    # Assign configuration variables
    username = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    # Setup connection with SmartHab API
    hub = pysmarthab.SmartHab()

    try:
        await hub.async_login(username, password)
    except pysmarthab.RequestFailedException as err:
        _LOGGER.exception("Error while trying to reach SmartHab API")
        raise ConfigEntryNotReady from err

    # Pass hub object to child platforms
    opp.data[DOMAIN][entry.entry_id] = {DATA_HUB: hub}

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload config entry from SmartHab integration."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
