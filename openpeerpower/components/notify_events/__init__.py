"""The notify_events component."""
import voluptuous as vol

from openpeerpower.const import CONF_TOKEN
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_TOKEN): cv.string})}, extra=vol.ALLOW_EXTRA
)


def setup(opp, config):
    """Set up the notify_events component."""

    opp.data[DOMAIN] = config[DOMAIN]
    discovery.load_platform(opp, "notify", DOMAIN, {}, config)
    return True
