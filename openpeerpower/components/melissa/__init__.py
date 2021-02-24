"""Support for Melissa climate."""
import melissa
import voluptuous as vol

from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.discovery import async_load_platform

DOMAIN = "melissa"
DATA_MELISSA = "MELISSA"


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


async def async_setup(opp, config):
    """Set up the Melissa Climate component."""
    conf = config[DOMAIN]
    username = conf.get(CONF_USERNAME)
    password = conf.get(CONF_PASSWORD)
    api = melissa.AsyncMelissa(username=username, password=password)
    await api.async_connect()
    opp.data[DATA_MELISSA] = api

    opp.async_create_task(async_load_platform(opp, "climate", DOMAIN, {}, config))
    return True
