"""The Sonarr component."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict

from sonarr import Sonarr, SonarrAccessRestricted, SonarrError

from openpeerpower.config_entries import SOURCE_REAUTH, ConfigEntry
from openpeerpower.const import (
    ATTR_NAME,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SOURCE,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_SOFTWARE_VERSION,
    CONF_BASE_PATH,
    CONF_UPCOMING_DAYS,
    CONF_WANTED_MAX_ITEMS,
    DATA_SONARR,
    DATA_UNDO_UPDATE_LISTENER,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_WANTED_MAX_ITEMS,
    DOMAIN,
)

PLATFORMS = ["sensor"]
SCAN_INTERVAL = timedelta(seconds=30)
_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPowerType, config: Dict) -> bool:
    """Set up the Sonarr component."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up Sonarr from a config entry."""
    if not entry.options:
        options = {
            CONF_UPCOMING_DAYS: entry.data.get(
                CONF_UPCOMING_DAYS, DEFAULT_UPCOMING_DAYS
            ),
            CONF_WANTED_MAX_ITEMS: entry.data.get(
                CONF_WANTED_MAX_ITEMS, DEFAULT_WANTED_MAX_ITEMS
            ),
        }
        opp.config_entries.async_update_entry(entry, options=options)

    sonarr = Sonarr(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data[CONF_API_KEY],
        base_path=entry.data[CONF_BASE_PATH],
        session=async_get_clientsession(opp),
        tls=entry.data[CONF_SSL],
        verify_ssl=entry.data[CONF_VERIFY_SSL],
    )

    try:
        await sonarr.update()
    except SonarrAccessRestricted:
        _async_start_reauth(opp, entry)
        return False
    except SonarrError as err:
        raise ConfigEntryNotReady from err

    undo_listener = entry.add_update_listener(_async_update_listener)

    opp.data[DOMAIN][entry.entry_id] = {
        DATA_SONARR: sonarr,
        DATA_UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

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

    opp.data[DOMAIN][entry.entry_id][DATA_UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _async_start_reauth(opp: OpenPeerPowerType, entry: ConfigEntry):
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_REAUTH},
            data={"config_entry_id": entry.entry_id, **entry.data},
        )
    )
    _LOGGER.error("API Key is no longer valid. Please reauthenticate")


async def _async_update_listener(opp: OpenPeerPowerType, entry: ConfigEntry) -> None:
    """Handle options update."""
    await opp.config_entries.async_reload(entry.entry_id)


class SonarrEntity(Entity):
    """Defines a base Sonarr entity."""

    def __init__(
        self,
        *,
        sonarr: Sonarr,
        entry_id: str,
        device_id: str,
        name: str,
        icon: str,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the Sonar entity."""
        self._entry_id = entry_id
        self._device_id = device_id
        self._enabled_default = enabled_default
        self._icon = icon
        self._name = name
        self.sonarr = sonarr

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about the application."""
        if self._device_id is None:
            return None

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_id)},
            ATTR_NAME: "Activity Sensor",
            ATTR_MANUFACTURER: "Sonarr",
            ATTR_SOFTWARE_VERSION: self.sonarr.app.info.version,
            "entry_type": "service",
        }
