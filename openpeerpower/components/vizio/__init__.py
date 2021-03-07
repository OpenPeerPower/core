"""The vizio component."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, List

from pyvizio.const import APPS
from pyvizio.util import gen_apps_list_from_url
import voluptuous as vol

from openpeerpower.components.media_player import DEVICE_CLASS_TV
from openpeerpower.config_entries import ENTRY_STATE_LOADED, SOURCE_IMPORT, ConfigEntry
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_APPS, CONF_DEVICE_CLASS, DOMAIN, VIZIO_SCHEMA

_LOGGER = logging.getLogger(__name__)


def validate_apps(config: ConfigType) -> ConfigType:
    """Validate CONF_APPS is only used when CONF_DEVICE_CLASS == DEVICE_CLASS_TV."""
    if (
        config.get(CONF_APPS) is not None
        and config[CONF_DEVICE_CLASS] != DEVICE_CLASS_TV
    ):
        raise vol.Invalid(
            f"'{CONF_APPS}' can only be used if {CONF_DEVICE_CLASS}' is '{DEVICE_CLASS_TV}'"
        )

    return config


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.All(VIZIO_SCHEMA, validate_apps)])},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["media_player"]


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Component setup, run import config flow for each entry in config."""
    if DOMAIN in config:
        for entry in config[DOMAIN]:
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=entry
                )
            )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry) -> bool:
    """Load the saved entities."""

    opp.data.setdefault(DOMAIN, {})
    if (
        CONF_APPS not in opp.data[DOMAIN]
        and config_entry.data[CONF_DEVICE_CLASS] == DEVICE_CLASS_TV
    ):
        coordinator = VizioAppsDataUpdateCoordinator(opp)
        await coordinator.async_refresh()
        opp.data[DOMAIN][CONF_APPS] = coordinator

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # Exclude this config entry because its not unloaded yet
    if not any(
        entry.state == ENTRY_STATE_LOADED
        and entry.entry_id != config_entry.entry_id
        and entry.data[CONF_DEVICE_CLASS] == DEVICE_CLASS_TV
        for entry in opp.config_entries.async_entries(DOMAIN)
    ):
        opp.data[DOMAIN].pop(CONF_APPS, None)

    if not opp.data[DOMAIN]:
        opp.data.pop(DOMAIN)

    return unload_ok


class VizioAppsDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Vizio app config data."""

    def __init__(self, opp: OpenPeerPowerType) -> None:
        """Initialize."""
        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(days=1),
            update_method=self._async_update_data,
        )
        self.data = APPS

    async def _async_update_data(self) -> List[Dict[str, Any]]:
        """Update data via library."""
        data = await gen_apps_list_from_url(session=async_get_clientsession(self.opp))
        if not data:
            raise UpdateFailed
        return sorted(data, key=lambda app: app["name"])
