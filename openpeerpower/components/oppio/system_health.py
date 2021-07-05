"""Provide info to system health."""
import os

from openpeerpower.components import system_health
from openpeerpower.core import OpenPeerPower, callback

SUPERVISOR_PING = f"http://{os.environ['OPPIO']}/supervisor/ping"
OBSERVER_URL = f"http://{os.environ['OPPIO']}:4357"


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info, "/oppio")


async def system_health_info(opp: OpenPeerPower):
    """Get info for the info page."""
    info = opp.components.oppio.get_info()
    host_info = opp.components.oppio.get_host_info()
    supervisor_info = opp.components.oppio.get_supervisor_info()

    if supervisor_info.get("healthy"):
        healthy = True
    else:
        healthy = {
            "type": "failed",
            "error": "Unhealthy",
            "more_info": "/oppio/system",
        }

    if supervisor_info.get("supported"):
        supported = True
    else:
        supported = {
            "type": "failed",
            "error": "Unsupported",
            "more_info": "/oppio/system",
        }

    information = {
        "host_os": host_info.get("operating_system"),
        "update_channel": info.get("channel"),
        "supervisor_version": f"supervisor-{info.get('supervisor')}",
        "docker_version": info.get("docker"),
        "disk_total": f"{host_info.get('disk_total')} GB",
        "disk_used": f"{host_info.get('disk_used')} GB",
        "healthy": healthy,
        "supported": supported,
    }

    if info.get("oppos") is not None:
        os_info = opp.components.oppio.get_os_info()
        information["board"] = os_info.get("board")

    information["supervisor_api"] = system_health.async_check_can_reach_url(
        opp, SUPERVISOR_PING, OBSERVER_URL
    )
    information["version_api"] = system_health.async_check_can_reach_url(
        opp,
        f"https://version.openpeerpower.io/{info.get('channel')}.json",
        "/oppio/system",
    )

    information["installed_addons"] = ", ".join(
        f"{addon['name']} ({addon['version']})"
        for addon in supervisor_info.get("addons", [])
    )

    return information
