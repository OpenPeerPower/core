"""Support for Xiaomi Miio."""
from datetime import timedelta
import logging

from miio.gateway import GatewayException

from openpeerpower import config_entries, core
from openpeerpower.const import CONF_HOST, CONF_TOKEN
from openpeerpower.helpers import device_registry as dr
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE,
    CONF_FLOW_TYPE,
    CONF_GATEWAY,
    CONF_MODEL,
    DOMAIN,
    KEY_COORDINATOR,
    MODELS_FAN,
    MODELS_SWITCH,
    MODELS_VACUUM,
)
from .gateway import ConnectXiaomiGateway

_LOGGER = logging.getLogger(__name__)

GATEWAY_PLATFORMS = ["alarm_control_panel", "sensor", "light"]
SWITCH_PLATFORMS = ["switch"]
FAN_PLATFORMS = ["fan"]
VACUUM_PLATFORMS = ["vacuum"]


async def async_setup(opp: core.OpenPeerPower, config: dict):
    """Set up the Xiaomi Miio component."""
    return True


async def async_setup_entry(opp: core.OpenPeerPower, entry: config_entries.ConfigEntry):
    """Set up the Xiaomi Miio components from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    if entry.data[CONF_FLOW_TYPE] == CONF_GATEWAY:
        if not await async_setup_gateway_entry(opp, entry):
            return False
    if entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        if not await async_setup_device_entry(opp, entry):
            return False

    return True


async def async_setup_gateway_entry(
    opp: core.OpenPeerPower, entry: config_entries.ConfigEntry
):
    """Set up the Xiaomi Gateway component from a config entry."""
    host = entry.data[CONF_HOST]
    token = entry.data[CONF_TOKEN]
    name = entry.title
    gateway_id = entry.unique_id

    # For backwards compat
    if entry.unique_id.endswith("-gateway"):
        opp.config_entries.async_update_entry(entry, unique_id=entry.data["mac"])

    # Connect to gateway
    gateway = ConnectXiaomiGateway(opp)
    if not await gateway.async_connect_gateway(host, token):
        return False
    gateway_info = gateway.gateway_info

    gateway_model = f"{gateway_info.model}-{gateway_info.hardware_version}"

    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, gateway_info.mac_address)},
        identifiers={(DOMAIN, gateway_id)},
        manufacturer="Xiaomi",
        name=name,
        model=gateway_model,
        sw_version=gateway_info.firmware_version,
    )

    async def async_update_data():
        """Fetch data from the subdevice."""
        try:
            for sub_device in gateway.gateway_device.devices.values():
                await opp.async_add_executor_job(sub_device.update)
        except GatewayException as ex:
            raise UpdateFailed("Got exception while fetching the state") from ex

    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        # Name of the data. For logging purposes.
        name=name,
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=10),
    )

    opp.data[DOMAIN][entry.entry_id] = {
        CONF_GATEWAY: gateway.gateway_device,
        KEY_COORDINATOR: coordinator,
    }

    for platform in GATEWAY_PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_setup_device_entry(
    opp: core.OpenPeerPower, entry: config_entries.ConfigEntry
):
    """Set up the Xiaomi Miio device component from a config entry."""
    model = entry.data[CONF_MODEL]

    # Identify platforms to setup
    platforms = []
    if model in MODELS_SWITCH:
        platforms = SWITCH_PLATFORMS
    elif model in MODELS_FAN:
        platforms = FAN_PLATFORMS
    for vacuum_model in MODELS_VACUUM:
        if model.startswith(vacuum_model):
            platforms = VACUUM_PLATFORMS

    if not platforms:
        return False

    for platform in platforms:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True
