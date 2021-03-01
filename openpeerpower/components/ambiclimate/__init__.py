"""Support for Ambiclimate devices."""
import voluptuous as vol

from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.helpers import config_validation as cv

from . import config_flow
from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up Ambiclimate components."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    config_flow.register_flow_implementation(
        opp, conf[CONF_CLIENT_ID], conf[CONF_CLIENT_SECRET]
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up Ambiclimate from a config entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, "climate")
    )

    return True
