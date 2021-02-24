"""Support to embed Sonos."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.media_player import DOMAIN as MP_DOMAIN
from openpeerpower.const import CONF_HOSTS
from openpeerpower.helpers import config_validation as cv

from .const import DOMAIN

CONF_ADVERTISE_ADDR = "advertise_addr"
CONF_INTERFACE_ADDR = "interface_addr"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                MP_DOMAIN: vol.Schema(
                    {
                        vol.Optional(CONF_ADVERTISE_ADDR): cv.string,
                        vol.Optional(CONF_INTERFACE_ADDR): cv.string,
                        vol.Optional(CONF_HOSTS): vol.All(
                            cv.ensure_list_csv, [cv.string]
                        ),
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Sonos component."""
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
    """Set up Sonos from a config entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, MP_DOMAIN)
    )
    return True
