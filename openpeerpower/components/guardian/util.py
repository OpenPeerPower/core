"""Define Guardian-specific utilities."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from datetime import timedelta
from typing import Callable

from aioguardian import Client
from aioguardian.errors import GuardianError

from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=30)


class GuardianDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Define an extended DataUpdateCoordinator with some Guardian goodies."""

    def __init__(
        self,
        opp: OpenPeerPower,
        *,
        client: Client,
        api_name: str,
        api_coro: Callable[..., Awaitable],
        api_lock: asyncio.Lock,
        valve_controller_uid: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            opp,
            LOGGER,
            name=f"{valve_controller_uid}_{api_name}",
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )

        self._api_coro = api_coro
        self._api_lock = api_lock
        self._client = client

    async def _async_update_data(self) -> dict:
        """Execute a "locked" API request against the valve controller."""
        async with self._api_lock, self._client:
            try:
                resp = await self._api_coro()
            except GuardianError as err:
                raise UpdateFailed(err) from err
        return resp["data"]
