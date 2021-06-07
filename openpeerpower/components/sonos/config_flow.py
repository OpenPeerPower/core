"""Config flow for SONOS."""
import pysonos

from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN


async def _async_has_devices(opp: OpenPeerPower) -> bool:
    """Return if there are devices that can be discovered."""
    result = await opp.async_add_executor_job(pysonos.discover)
    return bool(result)


config_entry_flow.register_discovery_flow(DOMAIN, "Sonos", _async_has_devices)
