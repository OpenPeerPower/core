"""Support for monitoring the local system."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import datetime
from functools import lru_cache
import logging
import os
import socket
import sys
from typing import Any, cast

import psutil
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA, SensorEntity
from openpeerpower.const import (
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_TYPE,
    DATA_GIBIBYTES,
    DATA_MEBIBYTES,
    DATA_RATE_MEGABYTES_PER_SECOND,
    DEVICE_CLASS_TIMESTAMP,
    EVENT_OPENPEERPOWER_STOP,
    PERCENTAGE,
    STATE_OFF,
    STATE_ON,
    TEMP_CELSIUS,
)
from openpeerpower.core import OpenPeerPower, callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity_component import DEFAULT_SCAN_INTERVAL
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.util import slugify
import openpeerpower.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

CONF_ARG = "arg"

if sys.maxsize > 2 ** 32:
    CPU_ICON = "mdi:cpu-64-bit"
else:
    CPU_ICON = "mdi:cpu-32-bit"

SENSOR_TYPE_NAME = 0
SENSOR_TYPE_UOM = 1
SENSOR_TYPE_ICON = 2
SENSOR_TYPE_DEVICE_CLASS = 3
SENSOR_TYPE_MANDATORY_ARG = 4

SIGNAL_SYSTEMMONITOR_UPDATE = "systemmonitor_update"

# Schema: [name, unit of measurement, icon, device class, flag if mandatory arg]
SENSOR_TYPES: dict[str, tuple[str, str | None, str | None, str | None, bool]] = {
    "disk_free": ("Disk free", DATA_GIBIBYTES, "mdi:harddisk", None, False),
    "disk_use": ("Disk use", DATA_GIBIBYTES, "mdi:harddisk", None, False),
    "disk_use_percent": (
        "Disk use (percent)",
        PERCENTAGE,
        "mdi:harddisk",
        None,
        False,
    ),
    "ipv4_address": ("IPv4 address", "", "mdi:server-network", None, True),
    "ipv6_address": ("IPv6 address", "", "mdi:server-network", None, True),
    "last_boot": ("Last boot", None, "mdi:clock", DEVICE_CLASS_TIMESTAMP, False),
    "load_15m": ("Load (15m)", " ", CPU_ICON, None, False),
    "load_1m": ("Load (1m)", " ", CPU_ICON, None, False),
    "load_5m": ("Load (5m)", " ", CPU_ICON, None, False),
    "memory_free": ("Memory free", DATA_MEBIBYTES, "mdi:memory", None, False),
    "memory_use": ("Memory use", DATA_MEBIBYTES, "mdi:memory", None, False),
    "memory_use_percent": (
        "Memory use (percent)",
        PERCENTAGE,
        "mdi:memory",
        None,
        False,
    ),
    "network_in": ("Network in", DATA_MEBIBYTES, "mdi:server-network", None, True),
    "network_out": ("Network out", DATA_MEBIBYTES, "mdi:server-network", None, True),
    "packets_in": ("Packets in", " ", "mdi:server-network", None, True),
    "packets_out": ("Packets out", " ", "mdi:server-network", None, True),
    "throughput_network_in": (
        "Network throughput in",
        DATA_RATE_MEGABYTES_PER_SECOND,
        "mdi:server-network",
        None,
        True,
    ),
    "throughput_network_out": (
        "Network throughput out",
        DATA_RATE_MEGABYTES_PER_SECOND,
        "mdi:server-network",
        None,
        True,
    ),
    "process": ("Process", " ", CPU_ICON, None, True),
    "processor_use": ("Processor use (percent)", PERCENTAGE, CPU_ICON, None, False),
    "processor_temperature": (
        "Processor temperature",
        TEMP_CELSIUS,
        CPU_ICON,
        None,
        False,
    ),
    "swap_free": ("Swap free", DATA_MEBIBYTES, "mdi:harddisk", None, False),
    "swap_use": ("Swap use", DATA_MEBIBYTES, "mdi:harddisk", None, False),
    "swap_use_percent": ("Swap use (percent)", PERCENTAGE, "mdi:harddisk", None, False),
}


def check_required_arg(value: Any) -> Any:
    """Validate that the required "arg" for the sensor types that need it are set."""
    for sensor in value:
        sensor_type = sensor[CONF_TYPE]
        sensor_arg = sensor.get(CONF_ARG)

        if sensor_arg is None and SENSOR_TYPES[sensor_type][SENSOR_TYPE_MANDATORY_ARG]:
            raise vol.RequiredFieldInvalid(
                f"Mandatory 'arg' is missing for sensor type '{sensor_type}'."
            )

    return value


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_RESOURCES, default={CONF_TYPE: "disk_use"}): vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_TYPE): vol.In(SENSOR_TYPES),
                        vol.Optional(CONF_ARG): cv.string,
                    }
                )
            ],
            check_required_arg,
        )
    }
)

IO_COUNTER = {
    "network_out": 0,
    "network_in": 1,
    "packets_out": 2,
    "packets_in": 3,
    "throughput_network_out": 0,
    "throughput_network_in": 1,
}

IF_ADDRS_FAMILY = {"ipv4_address": socket.AF_INET, "ipv6_address": socket.AF_INET6}

# There might be additional keys to be added for different
# platforms / hardware combinations.
# Taken from last version of "glances" integration before they moved to
# a generic temperature sensor logic.
# https://github.com/openpeerpower/core/blob/5e15675593ba94a2c11f9f929cdad317e27ce190/openpeerpower/components/glances/sensor.py#L199
CPU_SENSOR_PREFIXES = [
    "amdgpu 1",
    "aml_thermal",
    "Core 0",
    "Core 1",
    "CPU Temperature",
    "CPU",
    "cpu-thermal 1",
    "cpu_thermal 1",
    "exynos-therm 1",
    "Package id 0",
    "Physical id 0",
    "radeon 1",
    "soc-thermal 1",
    "soc_thermal 1",
    "Tctl",
    "cpu0-thermal",
]


@dataclass
class SensorData:
    """Data for a sensor."""

    argument: Any
    state: str | None
    value: Any | None
    update_time: datetime.datetime | None
    last_exception: BaseException | None


async def async_setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any | None = None,
) -> None:
    """Set up the system monitor sensors."""
    entities = []
    sensor_registry: dict[tuple[str, str], SensorData] = {}

    for resource in config[CONF_RESOURCES]:
        type_ = resource[CONF_TYPE]
        # Initialize the sensor argument if none was provided.
        # For disk monitoring default to "/" (root) to prevent runtime errors, if argument was not specified.
        if CONF_ARG not in resource:
            argument = ""
            if resource[CONF_TYPE].startswith("disk_"):
                argument = "/"
        else:
            argument = resource[CONF_ARG]

        # Verify if we can retrieve CPU / processor temperatures.
        # If not, do not create the entity and add a warning to the log
        if (
            type_ == "processor_temperature"
            and await opp.async_add_executor_job(_read_cpu_temperature) is None
        ):
            _LOGGER.warning("Cannot read CPU / processor temperature information")
            continue

        sensor_registry[(type_, argument)] = SensorData(
            argument, None, None, None, None
        )
        entities.append(SystemMonitorSensor(sensor_registry, type_, argument))

    scan_interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    await async_setup_sensor_registry_updates(opp, sensor_registry, scan_interval)

    async_add_entities(entities)


async def async_setup_sensor_registry_updates(
    opp: OpenPeerPower,
    sensor_registry: dict[tuple[str, str], SensorData],
    scan_interval: datetime.timedelta,
) -> None:
    """Update the registry and create polling."""

    _update_lock = asyncio.Lock()

    def _update_sensors() -> None:
        """Update sensors and store the result in the registry."""
        for (type_, argument), data in sensor_registry.items():
            try:
                state, value, update_time = _update(type_, data)
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error updating sensor: %s (%s)", type_, argument)
                data.last_exception = ex
            else:
                data.state = state
                data.value = value
                data.update_time = update_time
                data.last_exception = None

        # Only fetch these once per iteration as we use the same
        # data source multiple times in _update
        _disk_usage.cache_clear()
        _swap_memory.cache_clear()
        _virtual_memory.cache_clear()
        _net_io_counters.cache_clear()
        _net_if_addrs.cache_clear()
        _getloadavg.cache_clear()

    async def _async_update_data(*_: Any) -> None:
        """Update all sensors in one executor jump."""
        if _update_lock.locked():
            _LOGGER.warning(
                "Updating systemmonitor took longer than the scheduled update interval %s",
                scan_interval,
            )
            return

        async with _update_lock:
            await opp.async_add_executor_job(_update_sensors)
            async_dispatcher_send(opp, SIGNAL_SYSTEMMONITOR_UPDATE)

    polling_remover = async_track_time_interval(opp, _async_update_data, scan_interval)

    @callback
    def _async_stop_polling(*_: Any) -> None:
        polling_remover()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, _async_stop_polling)

    await _async_update_data()


class SystemMonitorSensor(SensorEntity):
    """Implementation of a system monitor sensor."""

    def __init__(
        self,
        sensor_registry: dict[tuple[str, str], SensorData],
        sensor_type: str,
        argument: str = "",
    ) -> None:
        """Initialize the sensor."""
        self._type: str = sensor_type
        self._name: str = f"{self.sensor_type[SENSOR_TYPE_NAME]} {argument}".rstrip()
        self._unique_id: str = slugify(f"{sensor_type}_{argument}")
        self._sensor_registry = sensor_registry
        self._argument: str = argument

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID."""
        return self._unique_id

    @property
    def device_class(self) -> str | None:
        """Return the class of this sensor."""
        return self.sensor_type[SENSOR_TYPE_DEVICE_CLASS]  # type: ignore[no-any-return]

    @property
    def icon(self) -> str | None:
        """Icon to use in the frontend, if any."""
        return self.sensor_type[SENSOR_TYPE_ICON]  # type: ignore[no-any-return]

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        return self.data.state

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        return self.sensor_type[SENSOR_TYPE_UOM]  # type: ignore[no-any-return]

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.data.last_exception is None

    @property
    def should_poll(self) -> bool:
        """Entity does not poll."""
        return False

    @property
    def sensor_type(self) -> list:
        """Return sensor type data for the sensor."""
        return SENSOR_TYPES[self._type]  # type: ignore

    @property
    def data(self) -> SensorData:
        """Return registry entry for the data."""
        return self._sensor_registry[(self._type, self._argument)]

    async def async_added_to_opp(self) -> None:
        """When entity is added to opp."""
        await super().async_added_to_opp()
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp, SIGNAL_SYSTEMMONITOR_UPDATE, self.async_write_op_state
            )
        )


def _update(  # noqa: C901
    type_: str, data: SensorData
) -> tuple[str | None, str | None, datetime.datetime | None]:
    """Get the latest system information."""
    state = None
    value = None
    update_time = None

    if type_ == "disk_use_percent":
        state = _disk_usage(data.argument).percent
    elif type_ == "disk_use":
        state = round(_disk_usage(data.argument).used / 1024 ** 3, 1)
    elif type_ == "disk_free":
        state = round(_disk_usage(data.argument).free / 1024 ** 3, 1)
    elif type_ == "memory_use_percent":
        state = _virtual_memory().percent
    elif type_ == "memory_use":
        virtual_memory = _virtual_memory()
        state = round((virtual_memory.total - virtual_memory.available) / 1024 ** 2, 1)
    elif type_ == "memory_free":
        state = round(_virtual_memory().available / 1024 ** 2, 1)
    elif type_ == "swap_use_percent":
        state = _swap_memory().percent
    elif type_ == "swap_use":
        state = round(_swap_memory().used / 1024 ** 2, 1)
    elif type_ == "swap_free":
        state = round(_swap_memory().free / 1024 ** 2, 1)
    elif type_ == "processor_use":
        state = round(psutil.cpu_percent(interval=None))
    elif type_ == "processor_temperature":
        state = _read_cpu_temperature()
    elif type_ == "process":
        state = STATE_OFF
        for proc in psutil.process_iter():
            try:
                if data.argument == proc.name():
                    state = STATE_ON
                    break
            except psutil.NoSuchProcess as err:
                _LOGGER.warning(
                    "Failed to load process with ID: %s, old name: %s",
                    err.pid,
                    err.name,
                )
    elif type_ in ["network_out", "network_in"]:
        counters = _net_io_counters()
        if data.argument in counters:
            counter = counters[data.argument][IO_COUNTER[type_]]
            state = round(counter / 1024 ** 2, 1)
        else:
            state = None
    elif type_ in ["packets_out", "packets_in"]:
        counters = _net_io_counters()
        if data.argument in counters:
            state = counters[data.argument][IO_COUNTER[type_]]
        else:
            state = None
    elif type_ in ["throughput_network_out", "throughput_network_in"]:
        counters = _net_io_counters()
        if data.argument in counters:
            counter = counters[data.argument][IO_COUNTER[type_]]
            now = dt_util.utcnow()
            if data.value and data.value < counter:
                state = round(
                    (counter - data.value)
                    / 1000 ** 2
                    / (now - (data.update_time or now)).total_seconds(),
                    3,
                )
            else:
                state = None
            update_time = now
            value = counter
        else:
            state = None
    elif type_ in ["ipv4_address", "ipv6_address"]:
        addresses = _net_if_addrs()
        if data.argument in addresses:
            for addr in addresses[data.argument]:
                if addr.family == IF_ADDRS_FAMILY[type_]:
                    state = addr.address
        else:
            state = None
    elif type_ == "last_boot":
        # Only update on initial setup
        if data.state is None:
            state = dt_util.utc_from_timestamp(psutil.boot_time()).isoformat()
        else:
            state = data.state
    elif type_ == "load_1m":
        state = round(_getloadavg()[0], 2)
    elif type_ == "load_5m":
        state = round(_getloadavg()[1], 2)
    elif type_ == "load_15m":
        state = round(_getloadavg()[2], 2)

    return state, value, update_time


# When we drop python 3.8 support these can be switched to
# @cache https://docs.python.org/3.9/library/functools.html#functools.cache
@lru_cache(maxsize=None)
def _disk_usage(path: str) -> Any:
    return psutil.disk_usage(path)


@lru_cache(maxsize=None)
def _swap_memory() -> Any:
    return psutil.swap_memory()


@lru_cache(maxsize=None)
def _virtual_memory() -> Any:
    return psutil.virtual_memory()


@lru_cache(maxsize=None)
def _net_io_counters() -> Any:
    return psutil.net_io_counters(pernic=True)


@lru_cache(maxsize=None)
def _net_if_addrs() -> Any:
    return psutil.net_if_addrs()


@lru_cache(maxsize=None)
def _getloadavg() -> tuple[float, float, float]:
    return os.getloadavg()


def _read_cpu_temperature() -> float | None:
    """Attempt to read CPU / processor temperature."""
    temps = psutil.sensors_temperatures()

    for name, entries in temps.items():
        for i, entry in enumerate(entries, start=1):
            # In case the label is empty (e.g. on Raspberry PI 4),
            # construct it ourself here based on the sensor key name.
            _label = f"{name} {i}" if not entry.label else entry.label
            # check both name and label because some systems embed cpu# in the
            # name, which makes label not match because label adds cpu# at end.
            if _label in CPU_SENSOR_PREFIXES or name in CPU_SENSOR_PREFIXES:
                return cast(float, round(entry.current, 1))

    return None
