"""Config flow flow LIFX."""
import aiolifx

from openpeerpower import config_entries
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN


async def _async_has_devices(opp):
    """Return if there are devices that can be discovered."""
    lifx_ip_addresses = await aiolifx.LifxScan(opp.loop).scan()
    return len(lifx_ip_addresses) > 0


config_entry_flow.register_discovery_flow(
    DOMAIN, "LIFX", _async_has_devices, config_entries.CONN_CLASS_LOCAL_POLL
)
