"""The awair component."""

from asyncio import gather
from typing import Any, Optional

from async_timeout import timeout
from python_awair import Awair
from python_awair.exceptions import AuthError

from openpeerpower.const import CONF_ACCESS_TOKEN
from openpeerpower.core import Config, OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_TIMEOUT, DOMAIN, LOGGER, UPDATE_INTERVAL, AwairResult

PLATFORMS = ["sensor"]


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up Awair integration."""
    return True


async def async_setup_entry(opp, config_entry) -> bool:
    """Set up Awair integration from a config entry."""
    session = async_get_clientsession(opp)
    coordinator = AwairDataUpdateCoordinator(opp, config_entry, session)

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][config_entry.entry_id] = coordinator

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp, config_entry) -> bool:
    """Unload Awair configuration."""
    tasks = []
    for platform in PLATFORMS:
        tasks.append(
            opp.config_entries.async_forward_entry_unload(config_entry, platform)
        )

    unload_ok = all(await gather(*tasks))
    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


class AwairDataUpdateCoordinator(DataUpdateCoordinator):
    """Define a wrapper class to update Awair data."""

    def __init__(self, opp, config_entry, session) -> None:
        """Set up the AwairDataUpdateCoordinator class."""
        access_token = config_entry.data[CONF_ACCESS_TOKEN]
        self._awair = Awair(access_token=access_token, session=session)
        self._config_entry = config_entry

        super().__init__(opp, LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self) -> Optional[Any]:
        """Update data via Awair client library."""
        with timeout(API_TIMEOUT):
            try:
                LOGGER.debug("Fetching users and devices")
                user = await self._awair.user()
                devices = await user.devices()
                results = await gather(
                    *[self._fetch_air_data(device) for device in devices]
                )
                return {result.device.uuid: result for result in results}
            except AuthError as err:
                flow_context = {
                    "source": "reauth",
                    "unique_id": self._config_entry.unique_id,
                }

                matching_flows = [
                    flow
                    for flow in self.opp.config_entries.flow.async_progress()
                    if flow["context"] == flow_context
                ]

                if not matching_flows:
                    self.opp.async_create_task(
                        self.opp.config_entries.flow.async_init(
                            DOMAIN,
                            context=flow_context,
                            data=self._config_entry.data,
                        )
                    )

                raise UpdateFailed(err) from err
            except Exception as err:
                raise UpdateFailed(err) from err

    async def _fetch_air_data(self, device):
        """Fetch latest air quality data."""
        LOGGER.debug("Fetching data for %s", device.uuid)
        air_data = await device.air_data_latest()
        LOGGER.debug(air_data)
        return AwairResult(device=device, air_data=air_data)
