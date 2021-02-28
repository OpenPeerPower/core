"""Provide info to system health."""
from openpeerpower.components import system_health
from openpeerpower.core import OpenPeerPower, callback


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(opp):
    """Get info for the info page."""
    return {
        "api_endpoint_reachable": system_health.async_check_can_reach_url(
            opp, "https://api.spotify.com"
        )
    }
