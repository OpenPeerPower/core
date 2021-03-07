"""The solaredge component."""
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_API_KEY, CONF_NAME
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import CONF_SITE_ID, DEFAULT_NAME, DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_SITE_ID): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Platform setup, do nothing."""
    if DOMAIN not in config:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(config[DOMAIN])
        )
    )
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Load the saved entities."""
    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, "sensor"))
    return True
