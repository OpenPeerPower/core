"""The Mazda Connected Services integration."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from pymazda import (
    Client as MazdaAPI,
    MazdaAccountLockedException,
    MazdaAPIEncryptionException,
    MazdaAuthenticationException,
    MazdaException,
    MazdaTokenExpiredException,
)

from openpeerpower.config_entries import SOURCE_REAUTH, ConfigEntry
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from openpeerpower.util.async_ import gather_with_concurrency

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Mazda Connected Services component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Mazda Connected Services from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    region = entry.data[CONF_REGION]

    websession = aiohttp_client.async_get_clientsession(opp)
    mazda_client = MazdaAPI(email, password, region, websession)

    try:
        await mazda_client.validate_credentials()
    except MazdaAuthenticationException:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_REAUTH},
                data=entry.data,
            )
        )
        return False
    except (
        MazdaException,
        MazdaAccountLockedException,
        MazdaTokenExpiredException,
        MazdaAPIEncryptionException,
    ) as ex:
        _LOGGER.error("Error occurred during Mazda login request: %s", ex)
        raise ConfigEntryNotReady from ex

    async def async_update_data():
        """Fetch data from Mazda API."""

        async def with_timeout(task):
            async with async_timeout.timeout(10):
                return await task

        try:
            vehicles = await with_timeout(mazda_client.get_vehicles())

            vehicle_status_tasks = [
                with_timeout(mazda_client.get_vehicle_status(vehicle["id"]))
                for vehicle in vehicles
            ]
            statuses = await gather_with_concurrency(5, *vehicle_status_tasks)

            for vehicle, status in zip(vehicles, statuses):
                vehicle["status"] = status

            return vehicles
        except MazdaAuthenticationException as ex:
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_REAUTH},
                    data=entry.data,
                )
            )
            raise UpdateFailed("Not authenticated with Mazda API") from ex
        except Exception as ex:
            _LOGGER.exception(
                "Unknown error occurred during Mazda update request: %s", ex
            )
            raise UpdateFailed(ex) from ex

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: mazda_client,
        DATA_COORDINATOR: coordinator,
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # Setup components
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


class MazdaEntity(CoordinatorEntity):
    """Defines a base Mazda entity."""

    def __init__(self, coordinator, index):
        """Initialize the Mazda entity."""
        super().__init__(coordinator)
        self.index = index
        self.vin = self.coordinator.data[self.index]["vin"]

    @property
    def device_info(self):
        """Return device info for the Mazda entity."""
        data = self.coordinator.data[self.index]
        return {
            "identifiers": {(DOMAIN, self.vin)},
            "name": self.get_vehicle_name(),
            "manufacturer": "Mazda",
            "model": f"{data['modelYear']} {data['carlineName']}",
        }

    def get_vehicle_name(self):
        """Return the vehicle name, to be used as a prefix for names of other entities."""
        data = self.coordinator.data[self.index]
        if "nickname" in data and len(data["nickname"]) > 0:
            return data["nickname"]
        return f"{data['modelYear']} {data['carlineName']}"
