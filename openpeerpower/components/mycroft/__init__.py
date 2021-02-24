"""Support for Mycroft AI."""
import voluptuous as vol

from openpeerpower.const import CONF_HOST
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv

DOMAIN = "mycroft"

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_HOST): cv.string})}, extra=vol.ALLOW_EXTRA
)


def setup(opp, config):
    """Set up the Mycroft component."""
    opp.data[DOMAIN] = config[DOMAIN][CONF_HOST]
    discovery.load_platform(opp, "notify", DOMAIN, {}, config)
    return True
