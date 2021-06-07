"""The syncthru component."""
from __future__ import annotations

from datetime import timedelta
import logging

import async_timeout
from pysyncthru import SyncThru

from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_URL
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client, device_registry as dr
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [BINARY_SENSOR_DOMAIN, SENSOR_DOMAIN]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up config entry."""

    session = aiohttp_client.async_get_clientsession(opp)
    opp.data.setdefault(DOMAIN, {})
    printer = SyncThru(entry.data[CONF_URL], session)

    async def async_update_data() -> SyncThru:
        """Fetch data from the printer."""
        try:
            async with async_timeout.timeout(10):
                await printer.update()
        except ValueError as value_error:
            # if an exception is thrown, printer does not support syncthru
            raise UpdateFailed(
                f"Configured printer at {printer.url} does not respond. "
                "Please make sure it supports SyncThru and check your configuration."
            ) from value_error
        else:
            if printer.is_unknown_state():
                raise ConfigEntryNotReady
            return printer

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )
    opp.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()

    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=device_connections(printer),
        identifiers=device_identifiers(printer),
        model=printer.model(),
        name=printer.hostname(),
    )

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    opp.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def device_identifiers(printer: SyncThru) -> set[tuple[str, str]] | None:
    """Get device identifiers for device registry."""
    serial = printer.serial_number()
    if serial is None:
        return None
    return {(DOMAIN, serial)}


def device_connections(printer: SyncThru) -> set[tuple[str, str]]:
    """Get device connections for device registry."""
    connections = set()
    try:
        mac = printer.raw()["identity"]["mac_addr"]
        if mac:
            connections.add((dr.CONNECTION_NETWORK_MAC, mac))
    except AttributeError:
        pass
    return connections
