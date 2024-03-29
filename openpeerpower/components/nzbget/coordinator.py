"""Provides the NZBGet DataUpdateCoordinator."""
from datetime import timedelta
import logging

from async_timeout import timeout
from pynzbgetapi import NZBGetAPI, NZBGetAPIException

from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class NZBGetDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NZBGet data."""

    def __init__(self, opp: OpenPeerPower, *, config: dict, options: dict) -> None:
        """Initialize global NZBGet data updater."""
        self.nzbget = NZBGetAPI(
            config[CONF_HOST],
            config.get(CONF_USERNAME),
            config.get(CONF_PASSWORD),
            config[CONF_SSL],
            config[CONF_VERIFY_SSL],
            config[CONF_PORT],
        )

        self._completed_downloads_init = False
        self._completed_downloads = {}

        update_interval = timedelta(seconds=options[CONF_SCAN_INTERVAL])

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    def _check_completed_downloads(self, history):
        """Check history for newly completed downloads."""
        actual_completed_downloads = {
            (x["Name"], x["Category"], x["Status"]) for x in history
        }

        if self._completed_downloads_init:
            tmp_completed_downloads = list(
                actual_completed_downloads.difference(self._completed_downloads)
            )

            for download in tmp_completed_downloads:
                self.opp.bus.fire(
                    "nzbget_download_complete",
                    {
                        "name": download[0],
                        "category": download[1],
                        "status": download[2],
                    },
                )

        self._completed_downloads = actual_completed_downloads
        self._completed_downloads_init = True

    async def _async_update_data(self) -> dict:
        """Fetch data from NZBGet."""

        def _update_data() -> dict:
            """Fetch data from NZBGet via sync functions."""
            status = self.nzbget.status()
            history = self.nzbget.history()

            self._check_completed_downloads(history)

            return {
                "status": status,
                "downloads": history,
            }

        try:
            async with timeout(4):
                return await self.opp.async_add_executor_job(_update_data)
        except NZBGetAPIException as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error
