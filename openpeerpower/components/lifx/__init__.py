"""Support for LIFX."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.const import CONF_PORT
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

CONF_SERVER = "server"
CONF_BROADCAST = "broadcast"

INTERFACE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SERVER): cv.string,
        vol.Optional(CONF_PORT): cv.port,
        vol.Optional(CONF_BROADCAST): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: {LIGHT_DOMAIN: vol.Schema(vol.All(cv.ensure_list, [INTERFACE_SCHEMA]))}},
    extra=vol.ALLOW_EXTRA,
)

DATA_LIFX_MANAGER = "lifx_manager"


async def async_setup(opp, config):
    """Set up the LIFX component."""
    conf = config.get(DOMAIN)

    opp.data[DOMAIN] = conf or {}

    if conf is not None:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp, entry):
    """Set up LIFX from a config entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, LIGHT_DOMAIN)
    )

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    opp.data.pop(DATA_LIFX_MANAGER).cleanup()

    await opp.config_entries.async_forward_entry_unload(entry, LIGHT_DOMAIN)

    return True
