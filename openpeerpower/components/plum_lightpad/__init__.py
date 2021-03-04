"""Support for Plum Lightpad devices."""
import logging

from aiohttp import ContentTypeError
from requests.exceptions import ConnectTimeout, HTTPError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN
from .utils import load_plum

_LOGGER = logging.getLogger(__name__)

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

PLATFORMS = ["light"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Plum Lightpad Platform initialization."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    _LOGGER.info("Found Plum Lightpad configuration in config, importing...")
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
        )
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Plum Lightpad from a config entry."""
    _LOGGER.debug("Setting up config entry with ID = %s", entry.unique_id)

    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)

    try:
        plum = await load_plum(username, password, opp)
    except ContentTypeError as ex:
        _LOGGER.error("Unable to authenticate to Plum cloud: %s", ex)
        return False
    except (ConnectTimeout, HTTPError) as ex:
        _LOGGER.error("Unable to connect to Plum cloud: %s", ex)
        raise ConfigEntryNotReady from ex

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = plum

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    def cleanup(event):
        """Clean up resources."""
        plum.cleanup()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, cleanup)
    return True
