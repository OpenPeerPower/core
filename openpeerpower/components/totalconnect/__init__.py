"""The totalconnect component."""
import asyncio
import logging

from total_connect_client import TotalConnectClient
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["alarm_control_panel", "binary_sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup.opp: OpenPeerPower, config: dict):
    """Set up by configuration file."""
    if DOMAIN not in config:
        return True

   .opp.async_create_task(
       .opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )

    return True


async def async_setup_entry.opp: OpenPeerPower, entry: ConfigEntry):
    """Set up upon config entry in user interface."""
   .opp.data.setdefault(DOMAIN, {})

    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    client = await opp..async_add_executor_job(
        TotalConnectClient.TotalConnectClient, username, password
    )

    if not client.is_valid_credentials():
        _LOGGER.error("TotalConnect authentication failed")
        return False

   .opp.data[DOMAIN][entry.entry_id] = client

    for component in PLATFORMS:
       .opp.async_create_task(
           .opp.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry.opp, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
               .opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
       .opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
