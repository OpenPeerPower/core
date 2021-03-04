"""Support for Nexia / Trane XL Thermostats."""
import asyncio
from datetime import timedelta
from functools import partial
import logging

from nexia.home import NexiaHome
from requests.exceptions import ConnectTimeout, HTTPError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, NEXIA_DEVICE, PLATFORMS, UPDATE_COORDINATOR
from .util import is_invalid_auth_code

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

DEFAULT_UPDATE_RATE = 120


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up the nexia component from YAML."""

    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Configure the base Nexia device for Open Peer Power."""

    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    state_file = opp.config.path(f"nexia_config_{username}.conf")

    try:
        nexia_home = await opp.async_add_executor_job(
            partial(
                NexiaHome,
                username=username,
                password=password,
                device_name=opp.config.location_name,
                state_file=state_file,
            )
        )
    except ConnectTimeout as ex:
        _LOGGER.error("Unable to connect to Nexia service: %s", ex)
        raise ConfigEntryNotReady from ex
    except HTTPError as http_ex:
        if is_invalid_auth_code(http_ex.response.status_code):
            _LOGGER.error(
                "Access error from Nexia service, please check credentials: %s", http_ex
            )
            return False
        _LOGGER.error("HTTP error from Nexia service: %s", http_ex)
        raise ConfigEntryNotReady from http_ex

    async def _async_update_data():
        """Fetch data from API endpoint."""
        return await opp.async_add_executor_job(nexia_home.update)

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="Nexia update",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=DEFAULT_UPDATE_RATE),
    )

    opp.data[DOMAIN][entry.entry_id] = {
        NEXIA_DEVICE: nexia_home,
        UPDATE_COORDINATOR: coordinator,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
