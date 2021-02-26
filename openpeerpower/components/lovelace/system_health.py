"""Provide info to system health."""
import asyncio

from openpeerpower.components import system_health
from openpeerpower.const import CONF_MODE
from openpeerpower.core import OpenPeerPower, callback

from .const import DOMAIN, MODE_AUTO, MODE_STORAGE, MODE_YAML


@callback
def async_register(
    opp: OpenPeerPower, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info, "/config/lovelace")


async def system_health_info(opp):
    """Get info for the info page."""
    health_info = {"dashboards": len(opp.data[DOMAIN]["dashboards"])}
    health_info.update(await opp.data[DOMAIN]["resources"].async_get_info())

    dashboards_info = await asyncio.gather(
        *[
            opp.data[DOMAIN]["dashboards"][dashboard].async_get_info()
            for dashboard in opp.data[DOMAIN]["dashboards"]
        ]
    )

    modes = set()
    for dashboard in dashboards_info:
        for key in dashboard:
            if isinstance(dashboard[key], int):
                health_info[key] = health_info.get(key, 0) + dashboard[key]
            elif key == CONF_MODE:
                modes.add(dashboard[key])
            else:
                health_info[key] = dashboard[key]

    if MODE_STORAGE in modes:
        health_info[CONF_MODE] = MODE_STORAGE
    elif MODE_YAML in modes:
        health_info[CONF_MODE] = MODE_YAML
    else:
        health_info[CONF_MODE] = MODE_AUTO

    return health_info
