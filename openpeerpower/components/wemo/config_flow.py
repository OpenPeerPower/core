"""Config flow for Wemo."""

import pywemo

from openpeerpower import config_entries
from openpeerpower.helpers import config_entry_flow

from . import DOMAIN


async def _async_has_devices(opp):
    """Return if there are devices that can be discovered."""
    return bool(await opp.async_add_executor_job(pywemo.discover_devices))


config_entry_flow.register_discovery_flow(
    DOMAIN, "Wemo", _async_has_devices, config_entries.CONN_CLASS_LOCAL_PUSH
)
