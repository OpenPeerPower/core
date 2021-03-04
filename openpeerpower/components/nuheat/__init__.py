"""Support for NuHeat thermostats."""
import asyncio
from datetime import timedelta
import logging

import nuheat
import requests

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_SERIAL_NUMBER, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the NuHeat component."""
    opp.data.setdefault(DOMAIN, {})
    return True


def _get_thermostat(api, serial_number):
    """Authenticate and create the thermostat object."""
    api.authenticate()
    return api.get_thermostat(serial_number)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up NuHeat from a config entry."""

    conf = entry.data

    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]
    serial_number = conf[CONF_SERIAL_NUMBER]

    api = nuheat.NuHeat(username, password)

    try:
        thermostat = await opp.async_add_executor_job(
            _get_thermostat, api, serial_number
        )
    except requests.exceptions.Timeout as ex:
        raise ConfigEntryNotReady from ex
    except requests.exceptions.HTTPError as ex:
        if (
            ex.response.status_code > HTTP_BAD_REQUEST
            and ex.response.status_code < HTTP_INTERNAL_SERVER_ERROR
        ):
            _LOGGER.error("Failed to login to nuheat: %s", ex)
            return False
        raise ConfigEntryNotReady from ex
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.error("Failed to login to nuheat: %s", ex)
        return False

    async def _async_update_data():
        """Fetch data from API endpoint."""
        await opp.async_add_executor_job(thermostat.get_data)

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=f"nuheat {serial_number}",
        update_method=_async_update_data,
        update_interval=timedelta(minutes=5),
    )

    opp.data[DOMAIN][entry.entry_id] = (thermostat, coordinator)

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
