"""The Unify Circuit component."""
import voluptuous as vol

from openpeerpower.const import CONF_NAME, CONF_URL
from openpeerpower.helpers import config_validation as cv, discovery

DOMAIN = "circuit"
CONF_WEBHOOK = "webhook"

WEBHOOK_SCHEMA = vol.Schema(
    {vol.Optional(CONF_NAME): cv.string, vol.Required(CONF_URL): cv.string}
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_WEBHOOK): vol.All(cv.ensure_list, [WEBHOOK_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Unify Circuit component."""
    webhooks = config[DOMAIN][CONF_WEBHOOK]

    for webhook_conf in webhooks:
        opp.async_create_task(
            discovery.async_load_platform(opp, "notify", DOMAIN, webhook_conf, config)
        )

    return True
