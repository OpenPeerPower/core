"""The profiler integration."""
import asyncio
import cProfile
from datetime import timedelta
import logging
import time

from guppy import hpy
import objgraph
from pyprof2calltree import convert
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, ServiceCall
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.service import async_register_admin_service
from openpeerpower.helpers.typing import ConfigType

from .const import DOMAIN

SERVICE_START = "start"
SERVICE_MEMORY = "memory"
SERVICE_START_LOG_OBJECTS = "start_log_objects"
SERVICE_STOP_LOG_OBJECTS = "stop_log_objects"
SERVICE_DUMP_LOG_OBJECTS = "dump_log_objects"

SERVICES = (
    SERVICE_START,
    SERVICE_MEMORY,
    SERVICE_START_LOG_OBJECTS,
    SERVICE_STOP_LOG_OBJECTS,
    SERVICE_DUMP_LOG_OBJECTS,
)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

CONF_SECONDS = "seconds"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TYPE = "type"

LOG_INTERVAL_SUB = "log_interval_subscription"

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the profiler component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Profiler from a config entry."""

    lock = asyncio.Lock()
    domain_data = opp.data[DOMAIN] = {}

    async def _async_run_profile(call: ServiceCall):
        async with lock:
            await _async_generate_profile(opp, call)

    async def _async_run_memory_profile(call: ServiceCall):
        async with lock:
            await _async_generate_memory_profile(opp, call)

    async def _async_start_log_objects(call: ServiceCall):
        if LOG_INTERVAL_SUB in domain_data:
            domain_data[LOG_INTERVAL_SUB]()

        opp.components.persistent_notification.async_create(
            "Object growth logging has started. See [the logs](/config/logs) to track the growth of new objects.",
            title="Object growth logging started",
            notification_id="profile_object_logging",
        )
        await opp.async_add_executor_job(_log_objects)
        domain_data[LOG_INTERVAL_SUB] = async_track_time_interval(
            opp, _log_objects, call.data[CONF_SCAN_INTERVAL]
        )

    async def _async_stop_log_objects(call: ServiceCall):
        if LOG_INTERVAL_SUB not in domain_data:
            return

        opp.components.persistent_notification.async_dismiss("profile_object_logging")
        domain_data.pop(LOG_INTERVAL_SUB)()

    def _dump_log_objects(call: ServiceCall):
        obj_type = call.data[CONF_TYPE]

        _LOGGER.critical(
            "%s objects in memory: %s",
            obj_type,
            objgraph.by_type(obj_type),
        )

        opp.components.persistent_notification.create(
            f"Objects with type {obj_type} have been dumped to the log. See [the logs](/config/logs) to review the repr of the objects.",
            title="Object dump completed",
            notification_id="profile_object_dump",
        )

    async_register_admin_service(
        opp,
        DOMAIN,
        SERVICE_START,
        _async_run_profile,
        schema=vol.Schema(
            {vol.Optional(CONF_SECONDS, default=60.0): vol.Coerce(float)}
        ),
    )

    async_register_admin_service(
        opp,
        DOMAIN,
        SERVICE_MEMORY,
        _async_run_memory_profile,
        schema=vol.Schema(
            {vol.Optional(CONF_SECONDS, default=60.0): vol.Coerce(float)}
        ),
    )

    async_register_admin_service(
        opp,
        DOMAIN,
        SERVICE_START_LOG_OBJECTS,
        _async_start_log_objects,
        schema=vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period
            }
        ),
    )

    async_register_admin_service(
        opp,
        DOMAIN,
        SERVICE_STOP_LOG_OBJECTS,
        _async_stop_log_objects,
        schema=vol.Schema({}),
    )

    async_register_admin_service(
        opp,
        DOMAIN,
        SERVICE_DUMP_LOG_OBJECTS,
        _dump_log_objects,
        schema=vol.Schema({vol.Required(CONF_TYPE): str}),
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    for service in SERVICES:
        opp.services.async_remove(domain=DOMAIN, service=service)
    if LOG_INTERVAL_SUB in opp.data[DOMAIN]:
        opp.data[DOMAIN][LOG_INTERVAL_SUB]()
    opp.data.pop(DOMAIN)
    return True


async def _async_generate_profile(opp: OpenPeerPower, call: ServiceCall):
    start_time = int(time.time() * 1000000)
    opp.components.persistent_notification.async_create(
        "The profile has started. This notification will be updated when it is complete.",
        title="Profile Started",
        notification_id=f"profiler_{start_time}",
    )
    profiler = cProfile.Profile()
    profiler.enable()
    await asyncio.sleep(float(call.data[CONF_SECONDS]))
    profiler.disable()

    cprofile_path = opp.config.path(f"profile.{start_time}.cprof")
    callgrind_path = opp.config.path(f"callgrind.out.{start_time}")
    await opp.async_add_executor_job(
        _write_profile, profiler, cprofile_path, callgrind_path
    )
    opp.components.persistent_notification.async_create(
        f"Wrote cProfile data to {cprofile_path} and callgrind data to {callgrind_path}",
        title="Profile Complete",
        notification_id=f"profiler_{start_time}",
    )


async def _async_generate_memory_profile(opp: OpenPeerPower, call: ServiceCall):
    start_time = int(time.time() * 1000000)
    opp.components.persistent_notification.async_create(
        "The memory profile has started. This notification will be updated when it is complete.",
        title="Profile Started",
        notification_id=f"memory_profiler_{start_time}",
    )
    heap_profiler = hpy()
    heap_profiler.setref()
    await asyncio.sleep(float(call.data[CONF_SECONDS]))
    heap = heap_profiler.heap()

    heap_path = opp.config.path(f"heap_profile.{start_time}.hpy")
    await opp.async_add_executor_job(_write_memory_profile, heap, heap_path)
    opp.components.persistent_notification.async_create(
        f"Wrote heapy memory profile to {heap_path}",
        title="Profile Complete",
        notification_id=f"memory_profiler_{start_time}",
    )


def _write_profile(profiler, cprofile_path, callgrind_path):
    profiler.create_stats()
    profiler.dump_stats(cprofile_path)
    convert(profiler.getstats(), callgrind_path)


def _write_memory_profile(heap, heap_path):
    heap.byrcs.dump(heap_path)


def _log_objects(*_):
    _LOGGER.critical("Memory Growth: %s", objgraph.growth(limit=100))
