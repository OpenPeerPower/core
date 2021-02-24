"""Config flow for Gree."""
from openpeerpower import config_entries
from openpeerpower.helpers import config_entry_flow

from .bridge import DeviceHelper
from .const import DOMAIN


async def _async_has_devices(opp) -> bool:
    """Return if there are devices that can be discovered."""
    devices = await DeviceHelper.find_devices()
    return len(devices) > 0


config_entry_flow.register_discovery_flow(
    DOMAIN, "Gree Climate", _async_has_devices, config_entries.CONN_CLASS_LOCAL_POLL
)
