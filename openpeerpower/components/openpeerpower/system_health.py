"""Provide info to system health."""
from openpeerpower.components import system_health
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import system_info


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(opp):
    """Get info for the info page."""
    info = await system_info.async_get_system_info(opp)

    return {
        "version": f"core-{info.get('version')}",
        "installation_type": info.get("installation_type"),
        "dev": info.get("dev"),
        "oppio": info.get("oppio"),
        "docker": info.get("docker"),
        "virtualenv": info.get("virtualenv"),
        "python_version": info.get("python_version"),
        "os_name": info.get("os_name"),
        "os_version": info.get("os_version"),
        "arch": info.get("arch"),
        "timezone": info.get("timezone"),
    }
