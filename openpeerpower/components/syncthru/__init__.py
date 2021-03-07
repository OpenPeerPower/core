"""The syncthru component."""

import logging
from typing import Set, Tuple

from pysyncthru import SyncThru

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_URL
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client, device_registry as dr
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Set up."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up config entry."""

    session = aiohttp_client.async_get_clientsession(opp)
    printer = opp.data[DOMAIN][entry.entry_id] = SyncThru(entry.data[CONF_URL], session)

    try:
        await printer.update()
    except ValueError:
        _LOGGER.error(
            "Device at %s not appear to be a SyncThru printer, aborting setup",
            printer.url,
        )
        return False
    else:
        if printer.is_unknown_state():
            raise ConfigEntryNotReady

    device_registry = await dr.async_get_registry(opp)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=device_connections(printer),
        identifiers=device_identifiers(printer),
        model=printer.model(),
        name=printer.hostname(),
    )

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, SENSOR_DOMAIN)
    )
    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    await opp.config_entries.async_forward_entry_unload(entry, SENSOR_DOMAIN)
    opp.data[DOMAIN].pop(entry.entry_id, None)
    return True


def device_identifiers(printer: SyncThru) -> Set[Tuple[str, str]]:
    """Get device identifiers for device registry."""
    return {(DOMAIN, printer.serial_number())}


def device_connections(printer: SyncThru) -> Set[Tuple[str, str]]:
    """Get device connections for device registry."""
    connections = set()
    try:
        mac = printer.raw()["identity"]["mac_addr"]
        if mac:
            connections.add((dr.CONNECTION_NETWORK_MAC, mac))
    except AttributeError:
        pass
    return connections
