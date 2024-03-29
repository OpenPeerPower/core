"""The Enphase Envoy integration."""
from __future__ import annotations

from datetime import timedelta
import logging

import async_timeout
from envoy_reader.envoy_reader import EnvoyReader
import httpx

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed
from openpeerpower.helpers.httpx_client import get_async_client
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import COORDINATOR, DOMAIN, NAME, PLATFORMS, SENSORS

SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Enphase Envoy from a config entry."""

    config = entry.data
    name = config[CONF_NAME]

    envoy_reader = EnvoyReader(
        config[CONF_HOST],
        config[CONF_USERNAME],
        config[CONF_PASSWORD],
        inverters=True,
        async_client=get_async_client(opp),
    )

    async def async_update_data():
        """Fetch data from API endpoint."""
        data = {}
        async with async_timeout.timeout(30):
            try:
                await envoy_reader.getData()
            except httpx.HTTPStatusError as err:
                raise ConfigEntryAuthFailed from err
            except httpx.HTTPError as err:
                raise UpdateFailed(f"Error communicating with API: {err}") from err

            for condition in SENSORS:
                if condition != "inverters":
                    data[condition] = await getattr(envoy_reader, condition)()
                else:
                    data[
                        "inverters_production"
                    ] = await envoy_reader.inverters_production()

            _LOGGER.debug("Retrieved data from API: %s", data)

            return data

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name=f"envoy {name}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        envoy_reader.get_inverters = False
        await coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        COORDINATOR: coordinator,
        NAME: name,
    }

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
