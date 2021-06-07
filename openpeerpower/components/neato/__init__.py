"""Support for Neato botvac connected vacuum cleaners."""
from datetime import timedelta
import logging

from pybotvac import Account, Neato
from pybotvac.exceptions import NeatoException
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_TOKEN
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from openpeerpower.helpers import config_entry_oauth2_flow, config_validation as cv
from openpeerpower.helpers.typing import ConfigType
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


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
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


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up config entry."""
    if CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed

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

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigType) -> bool:
    """Unload config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[NEATO_DOMAIN].pop(entry.entry_id)

    return unload_ok


class NeatoHub:
    """A My Neato hub wrapper class."""

    def __init__(self, opp: OpenPeerPower, neato: Account) -> None:
        """Initialize the Neato hub."""
        self._opp = opp
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
