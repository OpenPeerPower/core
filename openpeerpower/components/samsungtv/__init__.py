"""The Samsung TV integration."""
import socket

import voluptuous as vol

from openpeerpower.components.media_player.const import DOMAIN as MP_DOMAIN
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT
import openpeerpower.helpers.config_validation as cv

from .const import CONF_ON_ACTION, DEFAULT_NAME, DOMAIN


def ensure_unique_hosts(value):
    """Validate that all configs have a unique host."""
    vol.Schema(vol.Unique("duplicate host entries found"))(
        [socket.gethostbyname(entry[CONF_HOST]) for entry in value]
    )
    return value


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                cv.deprecated(CONF_PORT),
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): cv.string,
                        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                        vol.Optional(CONF_PORT): cv.port,
                        vol.Optional(CONF_ON_ACTION): cv.SCRIPT_SCHEMA,
                    }
                ),
            ],
            ensure_unique_hosts,
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Samsung TV integration."""
    if DOMAIN in config:
        opp.data[DOMAIN] = {}
        for entry_config in config[DOMAIN]:
            ip_address = await opp.async_add_executor_job(
                socket.gethostbyname, entry_config[CONF_HOST]
            )
            opp.data[DOMAIN][ip_address] = {
                CONF_ON_ACTION: entry_config.get(CONF_ON_ACTION)
            }
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": "import"}, data=entry_config
                )
            )

    return True


async def async_setup_entry(opp, entry):
    """Set up the Samsung TV platform."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, MP_DOMAIN)
    )

    return True
