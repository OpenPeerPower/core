"""The Brother component."""
from __future__ import annotations

from datetime import timedelta
import logging

from brother import Brother, DictToObj, SnmpError, UnsupportedModel
import pysnmp.hlapi.asyncio as SnmpEngine

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_TYPE
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_CONFIG_ENTRY, DOMAIN, SNMP
from .utils import get_snmp_engine

PLATFORMS = ["sensor"]

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Brother from a config entry."""
    host = entry.data[CONF_HOST]
    kind = entry.data[CONF_TYPE]

    snmp_engine = get_snmp_engine(opp)

    coordinator = BrotherDataUpdateCoordinator(
        opp, host=host, kind=kind, snmp_engine=snmp_engine
    )
    await coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN].setdefault(DATA_CONFIG_ENTRY, {})
    opp.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id] = coordinator
    opp.data[DOMAIN][SNMP] = snmp_engine

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        opp.data[DOMAIN][DATA_CONFIG_ENTRY].pop(entry.entry_id)
        if not opp.data[DOMAIN][DATA_CONFIG_ENTRY]:
            opp.data[DOMAIN].pop(SNMP)
            opp.data[DOMAIN].pop(DATA_CONFIG_ENTRY)

    return unload_ok


class BrotherDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Brother data from the printer."""

    def __init__(
        self, opp: OpenPeerPower, host: str, kind: str, snmp_engine: SnmpEngine
    ) -> None:
        """Initialize."""
        self.brother = Brother(host, kind=kind, snmp_engine=snmp_engine)

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> DictToObj:
        """Update data via library."""
        try:
            data = await self.brother.async_update()
        except (ConnectionError, SnmpError, UnsupportedModel) as error:
            raise UpdateFailed(error) from error
        return data
