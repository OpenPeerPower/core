"""Support for the LiteJet lighting system."""
import asyncio
import logging

import pylitejet
from serial import SerialException
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_PORT
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv

from .const import CONF_EXCLUDE_NAMES, CONF_INCLUDE_SWITCHES, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {
                    vol.Required(CONF_PORT): cv.string,
                    vol.Optional(CONF_EXCLUDE_NAMES): vol.All(
                        cv.ensure_list, [cv.string]
                    ),
                    vol.Optional(CONF_INCLUDE_SWITCHES, default=False): cv.boolean,
                }
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


def setup(opp, config):
    """Set up the LiteJet component."""
    if DOMAIN in config and not opp.config_entries.async_entries(DOMAIN):
        # No config entry exists and configuration.yaml config exists, trigger the import flow.
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up LiteJet via a config entry."""
    port = entry.data[CONF_PORT]

    try:
        system = pylitejet.LiteJet(port)
    except SerialException as ex:
        _LOGGER.error("Error connecting to the LiteJet MCP at %s", port, exc_info=ex)
        raise ConfigEntryNotReady from ex

    opp.data[DOMAIN] = system

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a LiteJet config entry."""

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        opp.data[DOMAIN].close()
        opp.data.pop(DOMAIN)

    return unload_ok
