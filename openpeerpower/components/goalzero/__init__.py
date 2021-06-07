"""The Goal Zero Yeti integration."""
import logging

from goalzero import Yeti, exceptions

from openpeerpower.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from openpeerpower.components.switch import DOMAIN as DOMAIN_SWITCH
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DATA_KEY_API, DATA_KEY_COORDINATOR, DOMAIN, MIN_TIME_BETWEEN_UPDATES

_LOGGER = logging.getLogger(__name__)


PLATFORMS = [DOMAIN_BINARY_SENSOR, DOMAIN_SWITCH]


async def async_setup_entry(opp, entry):
    """Set up Goal Zero Yeti from a config entry."""
    name = entry.data[CONF_NAME]
    host = entry.data[CONF_HOST]

    session = async_get_clientsession(opp)
    api = Yeti(host, opp.loop, session)
    try:
        await api.init_connect()
    except exceptions.ConnectError as ex:
        _LOGGER.warning("Failed to connect: %s", ex)
        raise ConfigEntryNotReady from ex

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            await api.get_state()
        except exceptions.ConnectError as err:
            raise UpdateFailed(f"Failed to communicating with device {err}") from err

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=name,
        update_method=async_update_data,
        update_interval=MIN_TIME_BETWEEN_UPDATES,
    )
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_KEY_API: api,
        DATA_KEY_COORDINATOR: coordinator,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class YetiEntity(CoordinatorEntity):
    """Representation of a Goal Zero Yeti entity."""

    def __init__(self, api, coordinator, name, server_unique_id):
        """Initialize a Goal Zero Yeti entity."""
        super().__init__(coordinator)
        self.api = api
        self._name = name
        self._server_unique_id = server_unique_id
        self._device_class = None

    @property
    def device_info(self):
        """Return the device information of the entity."""
        info = {
            "identifiers": {(DOMAIN, self._server_unique_id)},
            "manufacturer": "Goal Zero",
            "name": self._name,
        }
        if self.api.sysdata:
            info["model"] = self.api.sysdata["model"]
        if self.api.data:
            info["sw_version"] = self.api.data["firmwareVersion"]
        return info

    @property
    def device_class(self):
        """Return the class of this device."""
        return self._device_class
