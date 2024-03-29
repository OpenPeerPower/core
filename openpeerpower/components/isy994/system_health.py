"""Provide info to system health."""
from pyisy import ISY

from openpeerpower.components import system_health
from openpeerpower.const import CONF_HOST
from openpeerpower.core import OpenPeerPower, callback

from .const import DOMAIN, ISY994_ISY, ISY_URL_POSTFIX


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(opp):
    """Get info for the info page."""

    health_info = {}
    config_entry_id = next(
        iter(opp.data[DOMAIN])
    )  # Only first ISY is supported for now
    isy: ISY = opp.data[DOMAIN][config_entry_id][ISY994_ISY]

    entry = opp.config_entries.async_get_entry(config_entry_id)
    health_info["host_reachable"] = await system_health.async_check_can_reach_url(
        opp, f"{entry.data[CONF_HOST]}{ISY_URL_POSTFIX}"
    )
    health_info["device_connected"] = isy.connected
    health_info["last_heartbeat"] = isy.websocket.last_heartbeat
    health_info["websocket_status"] = isy.websocket.status

    return health_info
