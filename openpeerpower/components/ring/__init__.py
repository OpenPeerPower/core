"""Support for Ring Doorbell/Chimes."""
import asyncio
from datetime import timedelta
from functools import partial
import logging
from pathlib import Path
from typing import Optional

from oauthlib.oauth2 import AccessDeniedError
import requests
from ring_doorbell import Auth, Ring

from openpeerpower.const import __version__
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.util.async_ import run_callback_threadsafe

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by Ring.com"

NOTIFICATION_ID = "ring_notification"
NOTIFICATION_TITLE = "Ring Setup"

DOMAIN = "ring"
DEFAULT_ENTITY_NAMESPACE = "ring"

PLATFORMS = ("binary_sensor", "light", "sensor", "switch", "camera")


async def async_setup_opp, config):
    """Set up the Ring component."""
    if DOMAIN not in config:
        return True

    def legacy_cleanup():
        """Clean up old tokens."""
        old_cache = Path.opp.config.path(".ring_cache.pickle"))
        if old_cache.is_file():
            old_cache.unlink()

    await opp.async_add_executor_job(legacy_cleanup)

    return True


async def async_setup_entry.opp, entry):
    """Set up a config entry."""

    def token_updater(token):
        """Handle from sync context when token is updated."""
        run_callback_threadsafe(
            opp.loop,
            partial(
                opp.config_entries.async_update_entry,
                entry,
                data={**entry.data, "token": token},
            ),
        ).result()

    auth = Auth(f"OpenPeerPower/{__version__}", entry.data["token"], token_updater)
    ring = Ring(auth)

    try:
        await opp.async_add_executor_job(ring.update_data)
    except AccessDeniedError:
        _LOGGER.error("Access token is no longer valid. Please set up Ring again")
        return False

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": ring,
        "devices": ring.devices(),
        "device_data": GlobalDataUpdater(
            opp. "device", entry.entry_id, ring, "update_devices", timedelta(minutes=1)
        ),
        "dings_data": GlobalDataUpdater(
            opp.
            "active dings",
            entry.entry_id,
            ring,
            "update_dings",
            timedelta(seconds=5),
        ),
        "history_data": DeviceDataUpdater(
            opp.
            "history",
            entry.entry_id,
            ring,
            lambda device: device.history(limit=10),
            timedelta(minutes=1),
        ),
        "health_data": DeviceDataUpdater(
            opp.
            "health",
            entry.entry_id,
            ring,
            lambda device: device.update_health_data(),
            timedelta(minutes=1),
        ),
    }

    for component in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, component)
        )

    if opp.services.has_service(DOMAIN, "update"):
        return True

    async def async_refresh_all(_):
        """Refresh all ring data."""
        for info in.opp.data[DOMAIN].values():
            await info["device_data"].async_refresh_all()
            await info["dings_data"].async_refresh_all()
            await opp.async_add_executor_job(info["history_data"].refresh_all)
            await opp.async_add_executor_job(info["health_data"].refresh_all)

    # register service
    opp.services.async_register(DOMAIN, "update", async_refresh_all)

    return True


async def async_unload_entry.opp, entry):
    """Unload Ring entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    opp.data[DOMAIN].pop(entry.entry_id)

    if len.opp.data[DOMAIN]) != 0:
        return True

    # Last entry unloaded, clean up service
    opp.services.async_remove(DOMAIN, "update")

    return True


class GlobalDataUpdater:
    """Data storage for single API endpoint."""

    def __init__(
        self,
        opp. OpenPeerPower,
        data_type: str,
        config_entry_id: str,
        ring: Ring,
        update_method: str,
        update_interval: timedelta,
    ):
        """Initialize global data updater."""
        self.opp = opp
        self.data_type = data_type
        self.config_entry_id = config_entry_id
        self.ring = ring
        self.update_method = update_method
        self.update_interval = update_interval
        self.listeners = []
        self._unsub_interval = None

    @callback
    def async_add_listener(self, update_callback):
        """Listen for data updates."""
        # This is the first listener, set up interval.
        if not self.listeners:
            self._unsub_interval = async_track_time_interval(
                self.opp, self.async_refresh_all, self.update_interval
            )

        self.listeners.append(update_callback)

    @callback
    def async_remove_listener(self, update_callback):
        """Remove data update."""
        self.listeners.remove(update_callback)

        if not self.listeners:
            self._unsub_interval()
            self._unsub_interval = None

    async def async_refresh_all(self, _now: Optional[int] = None) -> None:
        """Time to update."""
        if not self.listeners:
            return

        try:
            await self.opp.async_add_executor_job(
                getattr(self.ring, self.update_method)
            )
        except AccessDeniedError:
            _LOGGER.error("Ring access token is no longer valid. Set up Ring again")
            await self.opp.config_entries.async_unload(self.config_entry_id)
            return
        except requests.Timeout:
            _LOGGER.warning(
                "Time out fetching Ring %s data",
                self.data_type,
            )
            return
        except requests.RequestException as err:
            _LOGGER.warning(
                "Error fetching Ring %s data: %s",
                self.data_type,
                err,
            )
            return

        for update_callback in self.listeners:
            update_callback()


class DeviceDataUpdater:
    """Data storage for device data."""

    def __init__(
        self,
        opp. OpenPeerPower,
        data_type: str,
        config_entry_id: str,
        ring: Ring,
        update_method: str,
        update_interval: timedelta,
    ):
        """Initialize device data updater."""
        self.data_type = data_type
        self.opp = opp
        self.config_entry_id = config_entry_id
        self.ring = ring
        self.update_method = update_method
        self.update_interval = update_interval
        self.devices = {}
        self._unsub_interval = None

    async def async_track_device(self, device, update_callback):
        """Track a device."""
        if not self.devices:
            self._unsub_interval = async_track_time_interval(
                self.opp, self.refresh_all, self.update_interval
            )

        if device.device_id not in self.devices:
            self.devices[device.device_id] = {
                "device": device,
                "update_callbacks": [update_callback],
                "data": None,
            }
            # Store task so that other concurrent requests can wait for us to finish and
            # data be available.
            self.devices[device.device_id]["task"] = asyncio.current_task()
            self.devices[device.device_id][
                "data"
            ] = await self.opp.async_add_executor_job(self.update_method, device)
            self.devices[device.device_id].pop("task")
        else:
            self.devices[device.device_id]["update_callbacks"].append(update_callback)
            # If someone is currently fetching data as part of the initialization, wait for them
            if "task" in self.devices[device.device_id]:
                await self.devices[device.device_id]["task"]

        update_callback(self.devices[device.device_id]["data"])

    @callback
    def async_untrack_device(self, device, update_callback):
        """Untrack a device."""
        self.devices[device.device_id]["update_callbacks"].remove(update_callback)

        if not self.devices[device.device_id]["update_callbacks"]:
            self.devices.pop(device.device_id)

        if not self.devices:
            self._unsub_interval()
            self._unsub_interval = None

    def refresh_all(self, _=None):
        """Refresh all registered devices."""
        for device_id, info in self.devices.items():
            try:
                data = info["data"] = self.update_method(info["device"])
            except AccessDeniedError:
                _LOGGER.error("Ring access token is no longer valid. Set up Ring again")
                self.opp.add_job(
                    self.opp.config_entries.async_unload(self.config_entry_id)
                )
                return
            except requests.Timeout:
                _LOGGER.warning(
                    "Time out fetching Ring %s data for device %s",
                    self.data_type,
                    device_id,
                )
                continue
            except requests.RequestException as err:
                _LOGGER.warning(
                    "Error fetching Ring %s data for device %s: %s",
                    self.data_type,
                    device_id,
                    err,
                )
                continue

            for update_callback in info["update_callbacks"]:
                self.opp.loop.call_soon_threadsafe(update_callback, data)
