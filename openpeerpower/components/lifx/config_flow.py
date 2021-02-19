"""Config flow flow LIFX."""
import aiolifx

from openpeerpower import config_entries
from openpeerpowerr.helpers import config_entry_flow

from .const import DOMAIN


async def _async_op._devices.opp):
    """Return if there are devices that can be discovered."""
    lifx_ip_addresses = await aiolifx.LifxScan.opp.loop).scan()
    return len(lifx_ip_addresses) > 0


config_entry_flow.register_discovery_flow(
    DOMAIN, "LIFX", _async_op._devices, config_entries.CONN_CLASS_LOCAL_POLL
)
