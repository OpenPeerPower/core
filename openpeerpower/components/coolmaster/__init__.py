"""The Coolmaster integration."""
import logging

from pycoolmasternet_async import CoolMasterNet

from openpeerpower.components.climate import SCAN_INTERVAL
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DATA_INFO, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate"]


async def async_setup_entry(opp, entry):
    """Set up Coolmaster from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    coolmaster = CoolMasterNet(host, port)
    try:
        info = await coolmaster.info()
        if not info:
            raise ConfigEntryNotReady
    except (OSError, ConnectionRefusedError, TimeoutError) as error:
        raise ConfigEntryNotReady() from error
    coordinator = CoolmasterDataUpdateCoordinator(opp, coolmaster)
    opp.data.setdefault(DOMAIN, {})
    await coordinator.async_config_entry_first_refresh()
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_INFO: info,
        DATA_COORDINATOR: coordinator,
    }
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp, entry):
    """Unload a Coolmaster config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class CoolmasterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Coolmaster data."""

    def __init__(self, opp, coolmaster):
        """Initialize global Coolmaster data updater."""
        self._coolmaster = coolmaster

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from Coolmaster."""
        try:
            return await self._coolmaster.status()
        except (OSError, ConnectionRefusedError, TimeoutError) as error:
            raise UpdateFailed from error
