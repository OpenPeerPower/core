"""The Mazda Connected Services integration."""
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
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    OpenPeerPowerError,
)
from openpeerpower.helpers import aiohttp_client, device_registry
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from openpeerpower.util.async_ import gather_with_concurrency

from .const import DATA_CLIENT, DATA_COORDINATOR, DATA_VEHICLES, DOMAIN, SERVICES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["device_tracker", "lock", "sensor"]


async def with_timeout(task, timeout_seconds=10):
    """Run an async task with a timeout."""
    async with async_timeout.timeout(timeout_seconds):
        return await task


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Mazda Connected Services from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    region = entry.data[CONF_REGION]

    websession = aiohttp_client.async_get_clientsession(opp)
    mazda_client = MazdaAPI(email, password, region, websession)

    try:
        await mazda_client.validate_credentials()
    except MazdaAuthenticationException as ex:
        raise ConfigEntryAuthFailed from ex
    except (
        MazdaException,
        MazdaAccountLockedException,
        MazdaTokenExpiredException,
        MazdaAPIEncryptionException,
    ) as ex:
        _LOGGER.error("Error occurred during Mazda login request: %s", ex)
        raise ConfigEntryNotReady from ex

    async def async_handle_service_call(service_call=None):
        """Handle a service call."""
        # Get device entry from device registry
        dev_reg = device_registry.async_get(opp)
        device_id = service_call.data.get("device_id")
        device_entry = dev_reg.async_get(device_id)

        # Get vehicle VIN from device identifiers
        mazda_identifiers = [
            identifier
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        ]
        vin_identifier = next(iter(mazda_identifiers))
        vin = vin_identifier[1]

        # Get vehicle ID and API client from opp.data
        vehicle_id = 0
        api_client = None
        for entry_data in opp.data[DOMAIN].values():
            for vehicle in entry_data[DATA_VEHICLES]:
                if vehicle["vin"] == vin:
                    vehicle_id = vehicle["id"]
                    api_client = entry_data[DATA_CLIENT]

        if vehicle_id == 0 or api_client is None:
            raise OpenPeerPowerError("Vehicle ID not found")

        api_method = getattr(api_client, service_call.service)
        try:
            if service_call.service == "send_poi":
                latitude = service_call.data.get("latitude")
                longitude = service_call.data.get("longitude")
                poi_name = service_call.data.get("poi_name")
                await api_method(vehicle_id, latitude, longitude, poi_name)
            else:
                await api_method(vehicle_id)
        except Exception as ex:
            _LOGGER.exception("Error occurred during Mazda service call: %s", ex)
            raise OpenPeerPowerError(ex) from ex

    def validate_mazda_device_id(device_id):
        """Check that a device ID exists in the registry and has at least one 'mazda' identifier."""
        dev_reg = device_registry.async_get(opp)
        device_entry = dev_reg.async_get(device_id)

        if device_entry is None:
            raise vol.Invalid("Invalid device ID")

        mazda_identifiers = [
            identifier
            for identifier in device_entry.identifiers
            if identifier[0] == DOMAIN
        ]
        if len(mazda_identifiers) < 1:
            raise vol.Invalid("Device ID is not a Mazda vehicle")

        return device_id

    service_schema = vol.Schema(
        {vol.Required("device_id"): vol.All(cv.string, validate_mazda_device_id)}
    )

    service_schema_send_poi = service_schema.extend(
        {
            vol.Required("latitude"): cv.latitude,
            vol.Required("longitude"): cv.longitude,
            vol.Required("poi_name"): cv.string,
        }
    )

    async def async_update_data():
        """Fetch data from Mazda API."""
        try:
            vehicles = await with_timeout(mazda_client.get_vehicles())

            vehicle_status_tasks = [
                with_timeout(mazda_client.get_vehicle_status(vehicle["id"]))
                for vehicle in vehicles
            ]
            statuses = await gather_with_concurrency(5, *vehicle_status_tasks)

            for vehicle, status in zip(vehicles, statuses):
                vehicle["status"] = status

            opp.data[DOMAIN][entry.entry_id][DATA_VEHICLES] = vehicles

            return vehicles
        except MazdaAuthenticationException as ex:
            raise ConfigEntryAuthFailed("Not authenticated with Mazda API") from ex
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

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: mazda_client,
        DATA_COORDINATOR: coordinator,
        DATA_VEHICLES: [],
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Setup components
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    # Register services
    for service in SERVICES:
        if service == "send_poi":
            opp.services.async_register(
                DOMAIN,
                service,
                async_handle_service_call,
                schema=service_schema_send_poi,
            )
        else:
            opp.services.async_register(
                DOMAIN, service, async_handle_service_call, schema=service_schema
            )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Only remove services if it is the last config entry
    if len(opp.data[DOMAIN]) == 1:
        for service in SERVICES:
            opp.services.async_remove(DOMAIN, service)

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MazdaEntity(CoordinatorEntity):
    """Defines a base Mazda entity."""

    def __init__(self, client, coordinator, index):
        """Initialize the Mazda entity."""
        super().__init__(coordinator)
        self.client = client
        self.index = index
        self.vin = self.coordinator.data[self.index]["vin"]
        self.vehicle_id = self.coordinator.data[self.index]["id"]

    @property
    def data(self):
        """Shortcut to access coordinator data for the entity."""
        return self.coordinator.data[self.index]

    @property
    def device_info(self):
        """Return device info for the Mazda entity."""
        return {
            "identifiers": {(DOMAIN, self.vin)},
            "name": self.get_vehicle_name(),
            "manufacturer": "Mazda",
            "model": f"{self.data['modelYear']} {self.data['carlineName']}",
        }

    def get_vehicle_name(self):
        """Return the vehicle name, to be used as a prefix for names of other entities."""
        if "nickname" in self.data and len(self.data["nickname"]) > 0:
            return self.data["nickname"]
        return f"{self.data['modelYear']} {self.data['carlineName']}"
