"""Get the local IP address of the Open Peer Power instance."""
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN, PLATFORM

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.deprecated(CONF_NAME),
            vol.Schema({vol.Optional(CONF_NAME, default=DOMAIN): cv.string}),
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up local_ip from configuration.yaml."""
    conf = config.get(DOMAIN)
    if conf:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, data=conf, context={"source": SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up local_ip from a config entry."""
    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, PLATFORM))

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_forward_entry_unload(entry, PLATFORM)
