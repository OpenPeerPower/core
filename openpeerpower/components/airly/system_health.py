"""Provide info to system health."""
from airly import Airly

from openpeerpower.components import system_health
from openpeerpower.core import OpenPeerPower, callback

from .const import DOMAIN


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(opp):
    """Get info for the info page."""
    requests_remaining = list(opp.data[DOMAIN].values())[0].airly.requests_remaining
    requests_per_day = list(opp.data[DOMAIN].values())[0].airly.requests_per_day

    return {
        "can_reach_server": system_health.async_check_can_reach_url(
            opp, Airly.AIRLY_API_URL
        ),
        "requests_remaining": requests_remaining,
        "requests_per_day": requests_per_day,
    }
