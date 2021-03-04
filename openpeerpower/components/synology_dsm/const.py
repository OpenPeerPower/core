"""Constants for Synology DSM."""

from synology_dsm.api.core.security import SynoCoreSecurity
from synology_dsm.api.core.upgrade import SynoCoreUpgrade
from synology_dsm.api.core.utilization import SynoCoreUtilization
from synology_dsm.api.dsm.information import SynoDSMInformation
from synology_dsm.api.storage.storage import SynoStorage
from synology_dsm.api.surveillance_station import SynoSurveillanceStation

from openpeerpower.components.binary_sensor import DEVICE_CLASS_SAFETY
from openpeerpower.const import (
    DATA_MEGABYTES,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_TERABYTES,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    PERCENTAGE,
)

DOMAIN = "synology_dsm"
PLATFORMS = ["binary_sensor", "camera", "sensor", "switch"]
COORDINATOR_CAMERAS = "coordinator_cameras"
COORDINATOR_CENTRAL = "coordinator_central"
COORDINATOR_SWITCHES = "coordinator_switches"
SYSTEM_LOADED = "system_loaded"

# Entry keys
SYNO_API = "syno_api"
UNDO_UPDATE_LISTENER = "undo_update_listener"

# Configuration
CONF_SERIAL = "serial"
CONF_VOLUMES = "volumes"
CONF_DEVICE_TOKEN = "device_token"

DEFAULT_USE_SSL = True
DEFAULT_VERIFY_SSL = False
DEFAULT_PORT = 5000
DEFAULT_PORT_SSL = 5001
# Options
DEFAULT_SCAN_INTERVAL = 15  # min
DEFAULT_TIMEOUT = 10  # sec

ENTITY_UNIT_LOAD = "load"

ENTITY_NAME = "name"
ENTITY_UNIT = "unit"
ENTITY_ICON = "icon"
ENTITY_CLASS = "device_class"
ENTITY_ENABLE = "enable"

# Services
SERVICE_REBOOT = "reboot"
SERVICE_SHUTDOWN = "shutdown"
SERVICES = [
    SERVICE_REBOOT,
    SERVICE_SHUTDOWN,
]

# Entity keys should start with the API_KEY to fetch

# Binary sensors
UPGRADE_BINARY_SENSORS = {
    f"{SynoCoreUpgrade.API_KEY}:update_available": {
        ENTITY_NAME: "Update available",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:update",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}

SECURITY_BINARY_SENSORS = {
    f"{SynoCoreSecurity.API_KEY}:status": {
        ENTITY_NAME: "Security status",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_SAFETY,
        ENTITY_ENABLE: True,
    },
}

STORAGE_DISK_BINARY_SENSORS = {
    f"{SynoStorage.API_KEY}:disk_exceed_bad_sector_thr": {
        ENTITY_NAME: "Exceeded Max Bad Sectors",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_SAFETY,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:disk_below_remain_life_thr": {
        ENTITY_NAME: "Below Min Remaining Life",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_SAFETY,
        ENTITY_ENABLE: True,
    },
}

# Sensors
UTILISATION_SENSORS = {
    f"{SynoCoreUtilization.API_KEY}:cpu_other_load": {
        ENTITY_NAME: "CPU Utilization (Other)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_user_load": {
        ENTITY_NAME: "CPU Utilization (User)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_system_load": {
        ENTITY_NAME: "CPU Utilization (System)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_total_load": {
        ENTITY_NAME: "CPU Utilization (Total)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_1min_load": {
        ENTITY_NAME: "CPU Load Averarge (1 min)",
        ENTITY_UNIT: ENTITY_UNIT_LOAD,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_5min_load": {
        ENTITY_NAME: "CPU Load Averarge (5 min)",
        ENTITY_UNIT: ENTITY_UNIT_LOAD,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_15min_load": {
        ENTITY_NAME: "CPU Load Averarge (15 min)",
        ENTITY_UNIT: ENTITY_UNIT_LOAD,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_real_usage": {
        ENTITY_NAME: "Memory Usage (Real)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_size": {
        ENTITY_NAME: "Memory Size",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_cached": {
        ENTITY_NAME: "Memory Cached",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_available_swap": {
        ENTITY_NAME: "Memory Available (Swap)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_available_real": {
        ENTITY_NAME: "Memory Available (Real)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_total_swap": {
        ENTITY_NAME: "Memory Total (Swap)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_total_real": {
        ENTITY_NAME: "Memory Total (Real)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:network_up": {
        ENTITY_NAME: "Network Up",
        ENTITY_UNIT: DATA_RATE_KILOBYTES_PER_SECOND,
        ENTITY_ICON: "mdi:upload",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:network_down": {
        ENTITY_NAME: "Network Down",
        ENTITY_UNIT: DATA_RATE_KILOBYTES_PER_SECOND,
        ENTITY_ICON: "mdi:download",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}
STORAGE_VOL_SENSORS = {
    f"{SynoStorage.API_KEY}:volume_status": {
        ENTITY_NAME: "Status",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:checkbox-marked-circle-outline",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_size_total": {
        ENTITY_NAME: "Total Size",
        ENTITY_UNIT: DATA_TERABYTES,
        ENTITY_ICON: "mdi:chart-pie",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoStorage.API_KEY}:volume_size_used": {
        ENTITY_NAME: "Used Space",
        ENTITY_UNIT: DATA_TERABYTES,
        ENTITY_ICON: "mdi:chart-pie",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_percentage_used": {
        ENTITY_NAME: "Volume Used",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chart-pie",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_disk_temp_avg": {
        ENTITY_NAME: "Average Disk Temp",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_disk_temp_max": {
        ENTITY_NAME: "Maximum Disk Temp",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: False,
    },
}
STORAGE_DISK_SENSORS = {
    f"{SynoStorage.API_KEY}:disk_smart_status": {
        ENTITY_NAME: "Status (Smart)",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:checkbox-marked-circle-outline",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoStorage.API_KEY}:disk_status": {
        ENTITY_NAME: "Status",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:checkbox-marked-circle-outline",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:disk_temp": {
        ENTITY_NAME: "Temperature",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: True,
    },
}

INFORMATION_SENSORS = {
    f"{SynoDSMInformation.API_KEY}:temperature": {
        ENTITY_NAME: "temperature",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: True,
    },
    f"{SynoDSMInformation.API_KEY}:uptime": {
        ENTITY_NAME: "last boot",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TIMESTAMP,
        ENTITY_ENABLE: False,
    },
}

# Switch
SURVEILLANCE_SWITCH = {
    f"{SynoSurveillanceStation.HOME_MODE_API_KEY}:home_mode": {
        ENTITY_NAME: "home mode",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:home-account",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}


TEMP_SENSORS_KEYS = [
    "volume_disk_temp_avg",
    "volume_disk_temp_max",
    "disk_temp",
    "temperature",
]
