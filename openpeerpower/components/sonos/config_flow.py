"""Config flow for SONOS."""
import pysonos

from openpeerpower import config_entries
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN


async def _async_has_devices(opp):
    """Return if there are devices that can be discovered."""
    return await opp.async_add_executor_job(pysonos.discover)


config_entry_flow.register_discovery_flow(
    DOMAIN, "Sonos", _async_has_devices, config_entries.CONN_CLASS_LOCAL_PUSH
)
