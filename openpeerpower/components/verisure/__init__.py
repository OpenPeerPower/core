"""Support for Verisure devices."""
from __future__ import annotations

from contextlib import suppress
import os

from openpeerpower.components.alarm_control_panel import (
    DOMAIN as ALARM_CONTROL_PANEL_DOMAIN,
)
from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.camera import DOMAIN as CAMERA_DOMAIN
from openpeerpower.components.lock import DOMAIN as LOCK_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.storage import STORAGE_DIR

from .const import DOMAIN
from .coordinator import VerisureDataUpdateCoordinator

PLATFORMS = [
    ALARM_CONTROL_PANEL_DOMAIN,
    BINARY_SENSOR_DOMAIN,
    CAMERA_DOMAIN,
    LOCK_DOMAIN,
    SENSOR_DOMAIN,
    SWITCH_DOMAIN,
]

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Verisure from a config entry."""
    coordinator = VerisureDataUpdateCoordinator(opp, entry=entry)

    if not await coordinator.async_login():
        raise ConfigEntryAuthFailed

    entry.async_on_unload(
        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, coordinator.async_logout)
    )

    await coordinator.async_config_entry_first_refresh()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = coordinator

    # Set up all platforms for this device/entry.
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Verisure config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    cookie_file = opp.config.path(STORAGE_DIR, f"verisure_{entry.entry_id}")
    with suppress(FileNotFoundError):
        await opp.async_add_executor_job(os.unlink, cookie_file)

    del opp.data[DOMAIN][entry.entry_id]

    if not opp.data[DOMAIN]:
        del opp.data[DOMAIN]

    return True
