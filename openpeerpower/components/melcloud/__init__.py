"""The MELCloud Climate integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, List

from aiohttp import ClientConnectionError
from async_timeout import timeout
from pymelcloud import Device, get_devices
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_TOKEN, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util import Throttle

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

PLATFORMS = ["climate", "sensor", "water_heater"]

CONF_LANGUAGE = "language"
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_TOKEN): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPowerType, config: ConfigEntry):
    """Establish connection with MELCloud."""
    if DOMAIN not in config:
        return True

    username = config[DOMAIN][CONF_USERNAME]
    token = config[DOMAIN][CONF_TOKEN]
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_USERNAME: username, CONF_TOKEN: token},
        )
    )
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Establish connection with MELClooud."""
    conf = entry.data
    mel_devices = await mel_devices_setup(opp, conf[CONF_TOKEN])
    opp.data.setdefault(DOMAIN, {}).update({entry.entry_id: mel_devices})
    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )
    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    await asyncio.gather(
        *[
            opp.config_entries.async_forward_entry_unload(config_entry, platform)
            for platform in PLATFORMS
        ]
    )
    opp.data[DOMAIN].pop(config_entry.entry_id)
    if not opp.data[DOMAIN]:
        opp.data.pop(DOMAIN)
    return True


class MelCloudDevice:
    """MELCloud Device instance."""

    def __init__(self, device: Device):
        """Construct a device wrapper."""
        self.device = device
        self.name = device.name
        self._available = True

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Pull the latest data from MELCloud."""
        try:
            await self.device.update()
            self._available = True
        except ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.name)
            self._available = False

    async def async_set(self, properties: Dict[str, Any]):
        """Write state changes to the MELCloud API."""
        try:
            await self.device.set(properties)
            self._available = True
        except ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.name)
            self._available = False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_id(self):
        """Return device ID."""
        return self.device.device_id

    @property
    def building_id(self):
        """Return building ID of the device."""
        return self.device.building_id

    @property
    def device_info(self):
        """Return a device description for device registry."""
        _device_info = {
            "connections": {(CONNECTION_NETWORK_MAC, self.device.mac)},
            "identifiers": {(DOMAIN, f"{self.device.mac}-{self.device.serial}")},
            "manufacturer": "Mitsubishi Electric",
            "name": self.name,
        }
        unit_infos = self.device.units
        if unit_infos is not None:
            _device_info["model"] = ", ".join(
                [x["model"] for x in unit_infos if x["model"]]
            )
        return _device_info


async def mel_devices_setup(opp, token) -> List[MelCloudDevice]:
    """Query connected devices from MELCloud."""
    session = opp.helpers.aiohttp_client.async_get_clientsession()
    try:
        with timeout(10):
            all_devices = await get_devices(
                token,
                session,
                conf_update_interval=timedelta(minutes=5),
                device_set_debounce=timedelta(seconds=1),
            )
    except (asyncio.TimeoutError, ClientConnectionError) as ex:
        raise ConfigEntryNotReady() from ex

    wrapped_devices = {}
    for device_type, devices in all_devices.items():
        wrapped_devices[device_type] = [MelCloudDevice(device) for device in devices]
    return wrapped_devices
