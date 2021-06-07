"""Support for the Hive devices and services."""
from functools import wraps
import logging

from aiohttp.web_exceptions import HTTPException
from apyhiveapi import Hive
from apyhiveapi.helper.hive_exceptions import HiveReauthRequired
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client, config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity

from .const import DOMAIN, PLATFORM_LOOKUP, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): cv.string,
                    vol.Required(CONF_USERNAME): cv.string,
                    vol.Optional(CONF_SCAN_INTERVAL, default=2): cv.positive_int,
                },
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Hive configuration setup."""
    opp.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    if not opp.config_entries.async_entries(DOMAIN):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data={
                    CONF_USERNAME: conf[CONF_USERNAME],
                    CONF_PASSWORD: conf[CONF_PASSWORD],
                },
            )
        )
    return True


async def async_setup_entry(opp, entry):
    """Set up Hive from a config entry."""

    websession = aiohttp_client.async_get_clientsession(opp)
    hive = Hive(websession)
    hive_config = dict(entry.data)

    hive_config["options"] = {}
    hive_config["options"].update(
        {CONF_SCAN_INTERVAL: dict(entry.options).get(CONF_SCAN_INTERVAL, 120)}
    )
    opp.data[DOMAIN][entry.entry_id] = hive

    try:
        devices = await hive.session.startSession(hive_config)
    except HTTPException as error:
        _LOGGER.error("Could not connect to the internet: %s", error)
        raise ConfigEntryNotReady() from error
    except HiveReauthRequired as err:
        raise ConfigEntryAuthFailed from err

    for ha_type, hive_type in PLATFORM_LOOKUP.items():
        device_list = devices.get(hive_type)
        if device_list:
            opp.async_create_task(
                opp.config_entries.async_forward_entry_setup(entry, ha_type)
            )

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def refresh_system(func):
    """Force update all entities after state change."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        await func(self, *args, **kwargs)
        async_dispatcher_send(self.opp, DOMAIN)

    return wrapper


class HiveEntity(Entity):
    """Initiate Hive Base Class."""

    def __init__(self, hive, hive_device):
        """Initialize the instance."""
        self.hive = hive
        self.device = hive_device
        self.attributes = {}
        self._unique_id = f'{self.device["hiveID"]}-{self.device["hiveType"]}'

    async def async_added_to_opp(self):
        """When entity is added to Open Peer Power."""
        self.async_on_remove(
            async_dispatcher_connect(self.opp, DOMAIN, self.async_write_op_state)
        )
