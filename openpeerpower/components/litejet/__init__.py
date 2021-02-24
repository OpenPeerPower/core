"""Support for the LiteJet lighting system."""
from pylitejet import LiteJet
import voluptuous as vol

from openpeerpower.const import CONF_PORT
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv

CONF_EXCLUDE_NAMES = "exclude_names"
CONF_INCLUDE_SWITCHES = "include_switches"

DOMAIN = "litejet"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PORT): cv.string,
                vol.Optional(CONF_EXCLUDE_NAMES): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_INCLUDE_SWITCHES, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(opp, config):
    """Set up the LiteJet component."""

    url = config[DOMAIN].get(CONF_PORT)

    opp.data["litejet_system"] = LiteJet(url)
    opp.data["litejet_config"] = config[DOMAIN]

    discovery.load_platform(opp, "light", DOMAIN, {}, config)
    if config[DOMAIN].get(CONF_INCLUDE_SWITCHES):
        discovery.load_platform(opp, "switch", DOMAIN, {}, config)
    discovery.load_platform(opp, "scene", DOMAIN, {}, config)

    return True


def is_ignored(opp, name):
    """Determine if a load, switch, or scene should be ignored."""
    for prefix in.opp.data["litejet_config"].get(CONF_EXCLUDE_NAMES, []):
        if name.startswith(prefix):
            return True
    return False
