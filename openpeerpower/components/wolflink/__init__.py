"""The Wolf SmartSet Service integration."""
from datetime import timedelta
import logging

from httpx import ConnectError, ConnectTimeout
from wolf_smartset.token_auth import InvalidAuth
from wolf_smartset.wolf_client import FetchFailed, WolfClient

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    COORDINATOR,
    DEVICE_GATEWAY,
    DEVICE_ID,
    DEVICE_NAME,
    DOMAIN,
    PARAMETERS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Wolf SmartSet Service component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Wolf SmartSet Service from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    device_name = entry.data[DEVICE_NAME]
    device_id = entry.data[DEVICE_ID]
    gateway_id = entry.data[DEVICE_GATEWAY]
    _LOGGER.debug(
        "Setting up wolflink integration for device: %s (ID: %s, gateway: %s)",
        device_name,
        device_id,
        gateway_id,
    )

    wolf_client = WolfClient(username, password)

    try:
        parameters = await fetch_parameters(wolf_client, gateway_id, device_id)
    except InvalidAuth:
        _LOGGER.debug("Authentication failed")
        return False

    async def async_update_data():
        """Update all stored entities for Wolf SmartSet."""
        try:
            values = await wolf_client.fetch_value(gateway_id, device_id, parameters)
            return {v.value_id: v.value for v in values}
        except ConnectError as exception:
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception
        except FetchFailed as exception:
            raise UpdateFailed(
                f"Could not fetch values from server due to: {exception}"
            ) from exception
        except InvalidAuth as exception:
            raise UpdateFailed("Invalid authentication during update.") from exception

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="wolflink",
        update_method=async_update_data,
        update_interval=timedelta(minutes=1),
    )

    await coordinator.async_refresh()

    opp.data[DOMAIN][entry.entry_id] = {}
    opp.data[DOMAIN][entry.entry_id][PARAMETERS] = parameters
    opp.data[DOMAIN][entry.entry_id][COORDINATOR] = coordinator
    opp.data[DOMAIN][entry.entry_id][DEVICE_ID] = device_id

    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def fetch_parameters(client: WolfClient, gateway_id: int, device_id: int):
    """
    Fetch all available parameters with usage of WolfClient.

    By default Reglertyp entity is removed because API will not provide value for this parameter.
    """
    try:
        fetched_parameters = await client.fetch_parameters(gateway_id, device_id)
        return [param for param in fetched_parameters if param.name != "Reglertyp"]
    except (ConnectError, ConnectTimeout, FetchFailed) as exception:
        raise ConfigEntryNotReady(
            f"Error communicating with API: {exception}"
        ) from exception
