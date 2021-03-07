"""The motion_blinds component."""
import asyncio
from datetime import timedelta
import logging
from socket import timeout

from motionblinds import MotionMulticast

from openpeerpower import config_entries, core
from openpeerpower.const import CONF_API_KEY, CONF_HOST, EVENT_OPENPEERPOWER_STOP
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import device_registry as dr
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    KEY_COORDINATOR,
    KEY_GATEWAY,
    KEY_MULTICAST_LISTENER,
    MANUFACTURER,
    PLATFORMS,
)
from .gateway import ConnectMotionGateway

_LOGGER = logging.getLogger(__name__)


def setup(opp: core.OpenPeerPower, config: dict):
    """Set up the Motion Blinds component."""
    return True


async def async_setup_entry(opp: core.OpenPeerPower, entry: config_entries.ConfigEntry):
    """Set up the motion_blinds components from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    key = entry.data[CONF_API_KEY]

    # Create multicast Listener
    if KEY_MULTICAST_LISTENER not in opp.data[DOMAIN]:
        multicast = MotionMulticast()
        opp.data[DOMAIN][KEY_MULTICAST_LISTENER] = multicast
        # start listening for local pushes (only once)
        await opp.async_add_executor_job(multicast.Start_listen)

        # register stop callback to shutdown listening for local pushes
        def stop_motion_multicast(event):
            """Stop multicast thread."""
            _LOGGER.debug("Shutting down Motion Listener")
            multicast.Stop_listen()

        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, stop_motion_multicast)

    # Connect to motion gateway
    multicast = opp.data[DOMAIN][KEY_MULTICAST_LISTENER]
    connect_gateway_class = ConnectMotionGateway(opp, multicast)
    if not await connect_gateway_class.async_connect_gateway(host, key):
        raise ConfigEntryNotReady
    motion_gateway = connect_gateway_class.gateway_device

    def update_gateway():
        """Call all updates using one async_add_executor_job."""
        motion_gateway.Update()
        for blind in motion_gateway.device_list.values():
            try:
                blind.Update()
            except timeout:
                # let the error be logged and handled by the motionblinds library
                pass

    async def async_update_data():
        """Fetch data from the gateway and blinds."""
        try:
            await opp.async_add_executor_job(update_gateway)
        except timeout:
            # let the error be logged and handled by the motionblinds library
            pass

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        # Name of the data. For logging purposes.
        name=entry.title,
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=600),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    opp.data[DOMAIN][entry.entry_id] = {
        KEY_GATEWAY: motion_gateway,
        KEY_COORDINATOR: coordinator,
    }

    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, motion_gateway.mac)},
        identifiers={(DOMAIN, entry.unique_id)},
        manufacturer=MANUFACTURER,
        name=entry.title,
        model="Wi-Fi bridge",
        sw_version=motion_gateway.protocol,
    )

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(
    opp: core.OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    if len(opp.data[DOMAIN]) == 1:
        # No motion gateways left, stop Motion multicast
        _LOGGER.debug("Shutting down Motion Listener")
        multicast = opp.data[DOMAIN].pop(KEY_MULTICAST_LISTENER)
        await opp.async_add_executor_job(multicast.Stop_listen)

    return unload_ok
