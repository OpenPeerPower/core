"""The NZBGet integration."""
import asyncio

import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
)
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_SPEED,
    DATA_COORDINATOR,
    DATA_UNDO_UPDATE_LISTENER,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SPEED_LIMIT,
    DEFAULT_SSL,
    DOMAIN,
    SERVICE_PAUSE,
    SERVICE_RESUME,
    SERVICE_SET_SPEED,
)
from .coordinator import NZBGetDataUpdateCoordinator

PLATFORMS = ["sensor", "switch"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_USERNAME): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
                vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SPEED_LIMIT_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_SPEED, default=DEFAULT_SPEED_LIMIT): cv.positive_int}
)


async def async_setup(opp: OpenPeerPowerType, config: dict) -> bool:
    """Set up the NZBGet integration."""
    opp.data.setdefault(DOMAIN, {})

    if opp.config_entries.async_entries(DOMAIN):
        return True

    if DOMAIN in config:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up NZBGet from a config entry."""
    if not entry.options:
        options = {
            CONF_SCAN_INTERVAL: entry.data.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            ),
        }
        opp.config_entries.async_update_entry(entry, options=options)

    coordinator = NZBGetDataUpdateCoordinator(
        opp,
        config=entry.data,
        options=entry.options,
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    _async_register_services(opp, coordinator)

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
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
        opp.data[DOMAIN][entry.entry_id][DATA_UNDO_UPDATE_LISTENER]()
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _async_register_services(
    opp: OpenPeerPowerType,
    coordinator: NZBGetDataUpdateCoordinator,
) -> None:
    """Register integration-level services."""

    def pause(call) -> None:
        """Service call to pause downloads in NZBGet."""
        coordinator.nzbget.pausedownload()

    def resume(call) -> None:
        """Service call to resume downloads in NZBGet."""
        coordinator.nzbget.resumedownload()

    def set_speed(call) -> None:
        """Service call to rate limit speeds in NZBGet."""
        coordinator.nzbget.rate(call.data[ATTR_SPEED])

    opp.services.async_register(DOMAIN, SERVICE_PAUSE, pause, schema=vol.Schema({}))
    opp.services.async_register(DOMAIN, SERVICE_RESUME, resume, schema=vol.Schema({}))
    opp.services.async_register(
        DOMAIN, SERVICE_SET_SPEED, set_speed, schema=SPEED_LIMIT_SCHEMA
    )


async def _async_update_listener(opp: OpenPeerPowerType, entry: ConfigEntry) -> None:
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


class NZBGetEntity(CoordinatorEntity):
    """Defines a base NZBGet entity."""

    def __init__(
        self, *, entry_id: str, name: str, coordinator: NZBGetDataUpdateCoordinator
    ) -> None:
        """Initialize the NZBGet entity."""
        super().__init__(coordinator)
        self._name = name
        self._entry_id = entry_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name
