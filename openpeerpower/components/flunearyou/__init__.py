"""The flunearyou component."""
import asyncio
from datetime import timedelta
from functools import partial

from pyflunearyou import Client
from pyflunearyou.errors import FluNearYouError

from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE
from openpeerpower.helpers import aiohttp_client, config_validation as cv
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CATEGORY_CDC_REPORT,
    CATEGORY_USER_REPORT,
    DATA_COORDINATOR,
    DOMAIN,
    LOGGER,
)

DEFAULT_UPDATE_INTERVAL = timedelta(minutes=30)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

PLATFORMS = ["sensor"]


async def async_setup(opp, config):
    """Set up the Flu Near You component."""
    opp.data[DOMAIN] = {DATA_COORDINATOR: {}}
    return True


async def async_setup_entry(opp, config_entry):
    """Set up Flu Near You as config entry."""
    opp.data[DOMAIN][DATA_COORDINATOR][config_entry.entry_id] = {}

    websession = aiohttp_client.async_get_clientsession(opp)
    client = Client(websession)

    latitude = config_entry.data.get(CONF_LATITUDE, opp.config.latitude)
    longitude = config_entry.data.get(CONF_LONGITUDE, opp.config.longitude)

    async def async_update(api_category):
        """Get updated date from the API based on category."""
        try:
            if api_category == CATEGORY_CDC_REPORT:
                return await client.cdc_reports.status_by_coordinates(
                    latitude, longitude
                )
            return await client.user_reports.status_by_coordinates(latitude, longitude)
        except FluNearYouError as err:
            raise UpdateFailed(err) from err

    data_init_tasks = []
    for api_category in [CATEGORY_CDC_REPORT, CATEGORY_USER_REPORT]:
        coordinator = opp.data[DOMAIN][DATA_COORDINATOR][config_entry.entry_id][
            api_category
        ] = DataUpdateCoordinator(
            opp,
            LOGGER,
            name=f"{api_category} ({latitude}, {longitude})",
            update_interval=DEFAULT_UPDATE_INTERVAL,
            update_method=partial(async_update, api_category),
        )
        data_init_tasks.append(coordinator.async_refresh())

    await asyncio.gather(*data_init_tasks)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload an Flu Near You config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN][DATA_COORDINATOR].pop(config_entry.entry_id)

    return unload_ok
