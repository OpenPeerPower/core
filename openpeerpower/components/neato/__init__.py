"""Support for Neato botvac connected vacuum cleaners."""
import asyncio
from datetime import timedelta
import logging

from pybotvac import Account, Neato
from pybotvac.exceptions import NeatoException
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_REAUTH, ConfigEntry
from openpeerpower.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_SOURCE,
    CONF_TOKEN,
)
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_entry_oauth2_flow, config_validation as cv
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.util import Throttle

from . import api, config_flow
from .const import (
    NEATO_CONFIG,
    NEATO_DOMAIN,
    NEATO_LOGIN,
    NEATO_MAP_DATA,
    NEATO_PERSISTENT_MAPS,
    NEATO_ROBOTS,
)

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        NEATO_DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["camera", "vacuum", "switch", "sensor"]


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Set up the Neato component."""
    opp.data[NEATO_DOMAIN] = {}

    if NEATO_DOMAIN not in config:
        return True

    opp.data[NEATO_CONFIG] = config[NEATO_DOMAIN]
    vendor = Neato()
    config_flow.OAuth2FlowHandler.async_register_implementation(
        opp,
        api.NeatoImplementation(
            opp,
            NEATO_DOMAIN,
            config[NEATO_DOMAIN][CONF_CLIENT_ID],
            config[NEATO_DOMAIN][CONF_CLIENT_SECRET],
            vendor.auth_endpoint,
            vendor.token_endpoint,
        ),
    )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up config entry."""
    if CONF_TOKEN not in entry.data:
        # Init reauth flow
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                NEATO_DOMAIN,
                context={CONF_SOURCE: SOURCE_REAUTH},
            )
        )
        return False

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(opp, entry)
    )

    session = config_entry_oauth2_flow.OAuth2Session(opp, entry, implementation)

    neato_session = api.ConfigEntryAuth(opp, entry, session)
    opp.data[NEATO_DOMAIN][entry.entry_id] = neato_session
    hub = NeatoHub(opp, Account(neato_session))

    try:
        await opp.async_add_executor_job(hub.update_robots)
    except NeatoException as ex:
        _LOGGER.debug("Failed to connect to Neato API")
        raise ConfigEntryNotReady from ex

    opp.data[NEATO_LOGIN] = hub

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigType) -> bool:
    """Unload config entry."""
    unload_functions = (
        opp.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )

    unload_ok = all(await asyncio.gather(*unload_functions))
    if unload_ok:
        opp.data[NEATO_DOMAIN].pop(entry.entry_id)

    return unload_ok


class NeatoHub:
    """A My Neato hub wrapper class."""

    def __init__(self, opp: OpenPeerPowerType, neato: Account):
        """Initialize the Neato hub."""
        self._opp: OpenPeerPowerType = opp
        self.my_neato: Account = neato

    @Throttle(timedelta(minutes=1))
    def update_robots(self):
        """Update the robot states."""
        _LOGGER.debug("Running HUB.update_robots %s", self._opp.data.get(NEATO_ROBOTS))
        self._opp.data[NEATO_ROBOTS] = self.my_neato.robots
        self._opp.data[NEATO_PERSISTENT_MAPS] = self.my_neato.persistent_maps
        self._opp.data[NEATO_MAP_DATA] = self.my_neato.maps

    def download_map(self, url):
        """Download a new map image."""
        map_image_data = self.my_neato.get_map_image(url)
        return map_image_data
