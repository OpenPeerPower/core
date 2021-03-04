"""Helper to gather system info."""
import os
import platform
from typing import Any, Dict

from openpeerpower.const import __version__ as current_version
from openpeerpower.loader import bind_opp
from openpeerpower.util.package import is_virtual_env

from .typing import OpenPeerPowerType


@bind_opp
async def async_get_system_info(opp: OpenPeerPowerType) -> Dict[str, Any]:
    """Return info about the system."""
    info_object = {
        "installation_type": "Unknown",
        "version": current_version,
        "dev": "dev" in current_version,
        "oppio": opp.components.oppio.is_oppio(),
        "virtualenv": is_virtual_env(),
        "python_version": platform.python_version(),
        "docker": False,
        "arch": platform.machine(),
        "timezone": str(opp.config.time_zone),
        "os_name": platform.system(),
        "os_version": platform.release(),
    }

    if platform.system() == "Windows":
        info_object["os_version"] = platform.win32_ver()[0]
    elif platform.system() == "Darwin":
        info_object["os_version"] = platform.mac_ver()[0]
    elif platform.system() == "Linux":
        info_object["docker"] = os.path.isfile("/.dockerenv")

    # Determine installation type on current data
    if info_object["docker"]:
        info_object["installation_type"] = "Open Peer Power Container"
    elif is_virtual_env():
        info_object["installation_type"] = "Open Peer Power Core"

    # Enrich with Supervisor information
    if opp.components.oppio.is_oppio():
        info = opp.components.oppio.get_info()
        host = opp.components.oppio.get_host_info()

        info_object["supervisor"] = info.get("supervisor")
        info_object["host_os"] = host.get("operating_system")
        info_object["docker_version"] = info.get("docker")
        info_object["coppis"] = host.get("coppis")

        if info.get("oppos") is not None:
            info_object["installation_type"] = "Open Peer Power OS"
        else:
            info_object["installation_type"] = "Open Peer Power Supervised"

    return info_object
