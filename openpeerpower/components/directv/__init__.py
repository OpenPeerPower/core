"""The DirecTV integration."""
from __future__ import annotations

from datetime import timedelta

from directv import DIRECTV, DIRECTVError

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import ATTR_NAME, CONF_HOST
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity import DeviceInfo, Entity

from .const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SOFTWARE_VERSION,
    ATTR_VIA_DEVICE,
    DOMAIN,
)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

PLATFORMS = ["media_player", "remote"]
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up DirecTV from a config entry."""
    dtv = DIRECTV(entry.data[CONF_HOST], session=async_get_clientsession(opp))

    try:
        await dtv.update()
    except DIRECTVError as err:
        raise ConfigEntryNotReady from err

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = dtv

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class DIRECTVEntity(Entity):
    """Defines a base DirecTV entity."""

    def __init__(self, *, dtv: DIRECTV, name: str, address: str = "0") -> None:
        """Initialize the DirecTV entity."""
        self._address = address
        self._device_id = address if address != "0" else dtv.device.info.receiver_id
        self._is_client = address != "0"
        self._name = name
        self.dtv = dtv

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this DirecTV receiver."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_id)},
            ATTR_NAME: self.name,
            ATTR_MANUFACTURER: self.dtv.device.info.brand,
            ATTR_MODEL: None,
            ATTR_SOFTWARE_VERSION: self.dtv.device.info.version,
            ATTR_VIA_DEVICE: (DOMAIN, self.dtv.device.info.receiver_id),
        }
