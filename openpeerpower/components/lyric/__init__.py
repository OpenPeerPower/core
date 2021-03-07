"""The Honeywell Lyric integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, Optional

from aiolyric import Lyric
from aiolyric.objects.device import LyricDevice
from aiolyric.objects.location import LyricLocation
import async_timeout
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
    device_registry as dr,
)
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ConfigEntryLyricClient, LyricLocalOAuth2Implementation
from .config_flow import OAuth2FlowHandler
from .const import DOMAIN, LYRIC_EXCEPTIONS, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Honeywell Lyric component."""
    opp.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    opp.data[DOMAIN][CONF_CLIENT_ID] = config[DOMAIN][CONF_CLIENT_ID]

    OAuth2FlowHandler.async_register_implementation(
        opp,
        LyricLocalOAuth2Implementation(
            opp,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Honeywell Lyric from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(opp, entry)
    )

    session = aiohttp_client.async_get_clientsession(opp)
    oauth_session = config_entry_oauth2_flow.OAuth2Session(opp, entry, implementation)

    client = ConfigEntryLyricClient(session, oauth_session)

    client_id = opp.data[DOMAIN][CONF_CLIENT_ID]
    lyric = Lyric(client, client_id)

    async def async_update_data() -> Lyric:
        """Fetch data from Lyric."""
        try:
            async with async_timeout.timeout(60):
                await lyric.get_locations()
            return lyric
        except LYRIC_EXCEPTIONS as exception:
            raise UpdateFailed(exception) from exception

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="lyric_coordinator",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=120),
    )

    opp.data[DOMAIN][entry.entry_id] = coordinator

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
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
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class LyricEntity(CoordinatorEntity):
    """Defines a base Honeywell Lyric entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        location: LyricLocation,
        device: LyricDevice,
        key: str,
        name: str,
        icon: Optional[str],
    ) -> None:
        """Initialize the Honeywell Lyric entity."""
        super().__init__(coordinator)
        self._key = key
        self._name = name
        self._icon = icon
        self._location = location
        self._mac_id = device.macID
        self._device_name = device.name
        self._device_model = device.deviceModel
        self._update_thermostat = coordinator.data.update_thermostat

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        return self._key

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def location(self) -> LyricLocation:
        """Get the Lyric Location."""
        return self.coordinator.data.locations_dict[self._location.locationID]

    @property
    def device(self) -> LyricDevice:
        """Get the Lyric Device."""
        return self.location.devices_dict[self._mac_id]


class LyricDeviceEntity(LyricEntity):
    """Defines a Honeywell Lyric device entity."""

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this Honeywell Lyric instance."""
        return {
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._mac_id)},
            "manufacturer": "Honeywell",
            "model": self._device_model,
            "name": self._device_name,
        }
