"""The Philips TV integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any, Callable

from haphilipsjs import ConnectionFailure, PhilipsTV

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_API_VERSION,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from openpeerpower.core import CALLBACK_TYPE, Context, OpenPeerPower, OppJob, callback
from openpeerpower.helpers.debounce import Debouncer
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

PLATFORMS = ["media_player", "remote"]

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Philips TV from a config entry."""

    tvapi = PhilipsTV(
        entry.data[CONF_HOST],
        entry.data[CONF_API_VERSION],
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
    )

    coordinator = PhilipsTVDataUpdateCoordinator(opp, tvapi)

    await coordinator.async_refresh()
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = coordinator

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PluggableAction:
    """A pluggable action handler."""

    def __init__(self, update: Callable[[], None]) -> None:
        """Initialize."""
        self._update = update
        self._actions: dict[Any, AutomationActionType] = {}

    def __bool__(self):
        """Return if we have something attached."""
        return bool(self._actions)

    @callback
    def async_attach(self, action: AutomationActionType, variables: dict[str, Any]):
        """Attach a device trigger for turn on."""

        @callback
        def _remove():
            del self._actions[_remove]
            self._update()

        job = OppJob(action)

        self._actions[_remove] = (job, variables)
        self._update()

        return _remove

    async def async_run(self, opp: OpenPeerPower, context: Context | None = None):
        """Run all turn on triggers."""
        for job, variables in self._actions.values():
            opp.async_run_opp_job(job, variables, context)


class PhilipsTVDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Coordinator to update data."""

    def __init__(self, opp, api: PhilipsTV) -> None:
        """Set up the coordinator."""
        self.api = api
        self._notify_future: asyncio.Task | None = None

        @callback
        def _update_listeners():
            for update_callback in self._listeners:
                update_callback()

        self.turn_on = PluggableAction(_update_listeners)

        super().__init__(
            opp,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            request_refresh_debouncer=Debouncer(
                opp, LOGGER, cooldown=2.0, immediate=False
            ),
        )

    @property
    def _notify_wanted(self):
        """Return if the notify feature should be active.

        We only run it when TV is considered fully on. When powerstate is in standby, the TV
        will go in low power states and seemingly break the http server in odd ways.
        """
        return (
            self.api.on
            and self.api.powerstate == "On"
            and self.api.notify_change_supported
        )

    async def _notify_task(self):
        while self._notify_wanted:
            res = await self.api.notifyChange(130)
            if res:
                self.async_set_updated_data(None)
            elif res is None:
                LOGGER.debug("Aborting notify due to unexpected return")
                break

    @callback
    def _async_notify_stop(self):
        if self._notify_future:
            self._notify_future.cancel()
            self._notify_future = None

    @callback
    def _async_notify_schedule(self):
        if self._notify_future and not self._notify_future.done():
            return

        if self._notify_wanted:
            self._notify_future = asyncio.create_task(self._notify_task())

    @callback
    def async_remove_listener(self, update_callback: CALLBACK_TYPE) -> None:
        """Remove data update."""
        super().async_remove_listener(update_callback)
        if not self._listeners:
            self._async_notify_stop()

    @callback
    def _async_stop_refresh(self, event: asyncio.Event) -> None:
        super()._async_stop_refresh(event)
        self._async_notify_stop()

    @callback
    async def _async_update_data(self):
        """Fetch the latest data from the source."""
        try:
            await self.api.update()
            self._async_notify_schedule()
        except ConnectionFailure:
            pass
