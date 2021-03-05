"""Helpers to help coordinate updates."""
import asyncio
from datetime import datetime, timedelta
import logging
from time import monotonic
from typing import Any, Awaitable, Callable, Generic, List, Optional, TypeVar
import urllib.error

import aiohttp
import requests

from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import CALLBACK_TYPE, Event, OpenPeerPower, OppJob, callback
from openpeerpower.helpers import entity, event
from openpeerpower.util.dt import utcnow

from .debounce import Debouncer

REQUEST_REFRESH_DEFAULT_COOLDOWN = 10
REQUEST_REFRESH_DEFAULT_IMMEDIATE = True

T = TypeVar("T")

# mypy: disallow-any-generics


class UpdateFailed(Exception):
    """Raised when an update has failed."""


class DataUpdateCoordinator(Generic[T]):
    """Class to manage fetching data from single endpoint."""

    def __init__(
        self,
        opp: OpenPeerPower,
        logger: logging.Logger,
        *,
        name: str,
        update_interval: Optional[timedelta] = None,
        update_method: Optional[Callable[[], Awaitable[T]]] = None,
        request_refresh_debouncer: Optional[Debouncer] = None,
    ):
        """Initialize global data updater."""
        self.opp = opp
        self.logger = logger
        self.name = name
        self.update_method = update_method
        self.update_interval = update_interval

        self.data: Optional[T] = None

        self._listeners: List[CALLBACK_TYPE] = []
        self._job = OppJob(self._handle_refresh_interval)
        self._unsub_refresh: Optional[CALLBACK_TYPE] = None
        self._request_refresh_task: Optional[asyncio.TimerHandle] = None
        self.last_update_success = True

        if request_refresh_debouncer is None:
            request_refresh_debouncer = Debouncer(
                opp,
                logger,
                cooldown=REQUEST_REFRESH_DEFAULT_COOLDOWN,
                immediate=REQUEST_REFRESH_DEFAULT_IMMEDIATE,
                function=self.async_refresh,
            )
        else:
            request_refresh_debouncer.function = self.async_refresh

        self._debounced_refresh = request_refresh_debouncer

        self.opp.bus.async_listen_once(
            EVENT_OPENPEERPOWER_STOP, self._async_stop_refresh
        )

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> Callable[[], None]:
        """Listen for data updates."""
        schedule_refresh = not self._listeners

        self._listeners.append(update_callback)

        # This is the first listener, set up interval.
        if schedule_refresh:
            self._schedule_refresh()

        @callback
        def remove_listener() -> None:
            """Remove update listener."""
            self.async_remove_listener(update_callback)

        return remove_listener

    @callback
    def async_remove_listener(self, update_callback: CALLBACK_TYPE) -> None:
        """Remove data update."""
        self._listeners.remove(update_callback)

        if not self._listeners and self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

    @callback
    def _schedule_refresh(self) -> None:
        """Schedule a refresh."""
        if self.update_interval is None:
            return

        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

        # We _floor_ utcnow to create a schedule on a rounded second,
        # minimizing the time between the point and the real activation.
        # That way we obtain a constant update frequency,
        # as long as the update process takes less than a second
        self._unsub_refresh = event.async_track_point_in_utc_time(
            self.opp,
            self._job,
            utcnow().replace(microsecond=0) + self.update_interval,
        )

    async def _handle_refresh_interval(self, _now: datetime) -> None:
        """Handle a refresh interval occurrence."""
        self._unsub_refresh = None
        await self.async_refresh()

    async def async_request_refresh(self) -> None:
        """Request a refresh.

        Refresh will wait a bit to see if it can batch them.
        """
        await self._debounced_refresh.async_call()

    async def _async_update_data(self) -> Optional[T]:
        """Fetch the latest data from the source."""
        if self.update_method is None:
            raise NotImplementedError("Update method not implemented")
        return await self.update_method()

    async def async_refresh(self) -> None:
        """Refresh data."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

        self._debounced_refresh.async_cancel()
        start = monotonic()

        try:
            self.data = await self._async_update_data()

        except (asyncio.TimeoutError, requests.exceptions.Timeout):
            if self.last_update_success:
                self.logger.error("Timeout fetching %s data", self.name)
                self.last_update_success = False

        except (aiohttp.ClientError, requests.exceptions.RequestException) as err:
            if self.last_update_success:
                self.logger.error("Error requesting %s data: %s", self.name, err)
                self.last_update_success = False

        except urllib.error.URLError as err:
            if self.last_update_success:
                if err.reason == "timed out":
                    self.logger.error("Timeout fetching %s data", self.name)
                else:
                    self.logger.error("Error requesting %s data: %s", self.name, err)
                self.last_update_success = False

        except UpdateFailed as err:
            if self.last_update_success:
                self.logger.error("Error fetching %s data: %s", self.name, err)
                self.last_update_success = False

        except NotImplementedError as err:
            raise err

        except Exception as err:  # pylint: disable=broad-except
            self.last_update_success = False
            self.logger.exception(
                "Unexpected error fetching %s data: %s", self.name, err
            )

        else:
            if not self.last_update_success:
                self.last_update_success = True
                self.logger.info("Fetching %s data recovered", self.name)

        finally:
            self.logger.debug(
                "Finished fetching %s data in %.3f seconds",
                self.name,
                monotonic() - start,
            )
            if self._listeners:
                self._schedule_refresh()

        for update_callback in self._listeners:
            update_callback()

    @callback
    def async_set_updated_data(self, data: T) -> None:
        """Manually update data, notify listeners and reset refresh interval."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

        self._debounced_refresh.async_cancel()

        self.data = data
        self.last_update_success = True
        self.logger.debug(
            "Manually updated %s data",
            self.name,
        )

        if self._listeners:
            self._schedule_refresh()

        for update_callback in self._listeners:
            update_callback()

    @callback
    def _async_stop_refresh(self, _: Event) -> None:
        """Stop refreshing when Open Peer Power is stopping."""
        self.update_interval = None
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None


class CoordinatorEntity(entity.Entity):
    """A class for entities using DataUpdateCoordinator."""

    def __init__(self, coordinator: DataUpdateCoordinator[Any]) -> None:
        """Create the entity with a DataUpdateCoordinator."""
        self.coordinator = coordinator

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_opp(self) -> None:
        """When entity is added to opp."""
        await super().async_added_to_opp()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_op_state()

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """
        # Ignore manual update requests if the entity is disabled
        if not self.enabled:
            return

        await self.coordinator.async_request_refresh()
