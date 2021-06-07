"""Platform for the iZone AC."""
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_EXCLUDE
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.typing import ConfigType

from .const import DATA_CONFIG, IZONE
from .discovery import async_start_discovery_service, async_stop_discovery_service

PLATFORMS = ["climate"]

CONFIG_SCHEMA = vol.Schema(
    {
        IZONE: vol.Schema(
            {
                vol.Optional(CONF_EXCLUDE, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: ConfigType):
    """Register the iZone component config."""
    conf = config.get(IZONE)
    if not conf:
        return True

    opp.data[DATA_CONFIG] = conf

    # Explicitly added in the config file, create a config entry.
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            IZONE, context={"source": config_entries.SOURCE_IMPORT}
        )
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up from a config entry."""
    await async_start_discovery_service(opp)
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp, entry):
    """Unload the config entry and stop discovery process."""
    await async_stop_discovery_service(opp)
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
