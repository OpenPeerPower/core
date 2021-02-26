"""Provide info to system health."""
from accuweather.const import ENDPOINT

from openpeerpower.components import system_health
from openpeerpower.core import OpenPeerPower, callback

from .const import COORDINATOR, DOMAIN


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(opp):
    """Get info for the info page."""
    remaining_requests = list(opp.data[DOMAIN].values())[0][
        COORDINATOR
    ].accuweather.requests_remaining

    return {
        "can_reach_server": system_health.async_check_can_reach_url(opp, ENDPOINT),
        "remaining_requests": remaining_requests,
    }
