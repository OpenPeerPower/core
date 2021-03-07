"""Support for BSH Home Connect appliances."""

import asyncio
from datetime import timedelta
import logging

from requests import HTTPError
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_entry_oauth2_flow, config_validation as cv
from openpeerpower.util import Throttle

from . import api, config_flow
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["binary_sensor", "light", "sensor", "switch"]


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up Home Connect component."""
    opp.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    config_flow.OAuth2FlowHandler.async_register_implementation(
        opp,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            opp,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Home Connect from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(opp, entry)
    )

    hc_api = api.ConfigEntryAuth(opp, entry, implementation)

    opp.data[DOMAIN][entry.entry_id] = hc_api

    await update_all_devices(opp, entry)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
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


@Throttle(SCAN_INTERVAL)
async def update_all_devices(opp, entry):
    """Update all the devices."""
    data = opp.data[DOMAIN]
    hc_api = data[entry.entry_id]
    try:
        await opp.async_add_executor_job(hc_api.get_devices)
        for device_dict in hc_api.devices:
            await opp.async_add_executor_job(device_dict["device"].initialize)
    except HTTPError as err:
        _LOGGER.warning("Cannot update devices: %s", err.response.status_code)
