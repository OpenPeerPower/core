"""The 1-Wire component."""
import asyncio
import logging

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN, PLATFORMS
from .onewirehub import CannotConnect, OneWireHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a 1-Wire proxy for a config entry."""
    opp.data.setdefault(DOMAIN, {})

    onewirehub = OneWireHub(opp)
    try:
        await onewirehub.initialize(entry)
    except CannotConnect as exc:
        raise ConfigEntryNotReady() from exc

    opp.data[DOMAIN][entry.entry_id] = onewirehub

    async def cleanup_registry() -> None:
        # Get registries
        device_registry, entity_registry = await asyncio.gather(
            opp.helpers.device_registry.async_get_registry(),
            opp.helpers.entity_registry.async_get_registry(),
        )
        # Generate list of all device entries
        registry_devices = [
            entry.id
            for entry in dr.async_entries_for_config_entry(
                device_registry, entry.entry_id
            )
        ]
        # Remove devices that don't belong to any entity
        for device_id in registry_devices:
            if not er.async_entries_for_device(
                entity_registry, device_id, include_disabled_entities=True
            ):
                _LOGGER.debug(
                    "Removing device `%s` because it does not have any entities",
                    device_id,
                )
                device_registry.async_remove_device(device_id)

    async def start_platforms() -> None:
        """Start platforms and cleanup devices."""
        # wait until all required platforms are ready
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_setup(entry, platform)
                for platform in PLATFORMS
            ]
        )
        await cleanup_registry()

    opp.async_create_task(start_platforms())

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok
