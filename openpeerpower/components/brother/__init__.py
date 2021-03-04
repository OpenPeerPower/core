"""The Brother component."""
import asyncio
from datetime import timedelta
import logging

from brother import Brother, SnmpError, UnsupportedModel

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_TYPE
from openpeerpower.core import Config, OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_CONFIG_ENTRY, DOMAIN, SNMP
from .utils import get_snmp_engine

PLATFORMS = ["sensor"]

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: Config):
    """Set up the Brother component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Brother from a config entry."""
    host = entry.data[CONF_HOST]
    kind = entry.data[CONF_TYPE]

    snmp_engine = get_snmp_engine(opp)

    coordinator = BrotherDataUpdateCoordinator(
        opp, host=host, kind=kind, snmp_engine=snmp_engine
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN].setdefault(DATA_CONFIG_ENTRY, {})
    opp.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id] = coordinator
    opp.data[DOMAIN][SNMP] = snmp_engine

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
        opp.data[DOMAIN][DATA_CONFIG_ENTRY].pop(entry.entry_id)
        if not opp.data[DOMAIN][DATA_CONFIG_ENTRY]:
            opp.data[DOMAIN].pop(SNMP)
            opp.data[DOMAIN].pop(DATA_CONFIG_ENTRY)

    return unload_ok


class BrotherDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Brother data from the printer."""

    def __init__(self, opp, host, kind, snmp_engine):
        """Initialize."""
        self.brother = Brother(host, kind=kind, snmp_engine=snmp_engine)

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.brother.async_update()
        except (ConnectionError, SnmpError, UnsupportedModel) as error:
            raise UpdateFailed(error) from error
        return self.brother.data
