"""The songpal component."""
from collections import OrderedDict

import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv

from .const import CONF_ENDPOINT, DOMAIN

SONGPAL_CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(CONF_NAME): cv.string, vol.Required(CONF_ENDPOINT): cv.string}
)

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(DOMAIN): vol.All(cv.ensure_list, [SONGPAL_CONFIG_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["media_player"]


async def async_setup(opp: OpenPeerPower, config: OrderedDict) -> bool:
    """Set up songpal environment."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True
    for config_entry in conf:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config_entry,
            ),
        )
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up songpal media player."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload songpal media player."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
