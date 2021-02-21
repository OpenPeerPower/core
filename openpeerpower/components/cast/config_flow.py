"""Config flow for Cast."""
import functools

from pychromecast.discovery import discover_chromecasts, stop_discovery

from openpeerpower import config_entries
from openpeerpower.components import zeroconf
from openpeerpower.helpers import config_entry_flow

from .const import DOMAIN
from .helpers import ChromeCastZeroconf


async def _async_has_devices.opp):
    """
    Return if there are devices that can be discovered.

    This function will be called if no devices are already found through the zeroconf
    integration.
    """

    zeroconf_instance = ChromeCastZeroconf.get_zeroconf()
    if zeroconf_instance is None:
        zeroconf_instance = await zeroconf.async_get_instance.opp)

    casts, browser = await.opp.async_add_executor_job(
        functools.partial(discover_chromecasts, zeroconf_instance=zeroconf_instance)
    )
    stop_discovery(browser)
    return casts


config_entry_flow.register_discovery_flow(
    DOMAIN, "Google Cast", _async_has_devices, config_entries.CONN_CLASS_LOCAL_PUSH
)
