"""Services for Fritz integration."""
import logging

from openpeerpower.core import OpenPeerPower, ServiceCall
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers.service import async_extract_config_entry_ids

from .const import DOMAIN, FRITZ_SERVICES, SERVICE_REBOOT, SERVICE_RECONNECT

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(opp: OpenPeerPower):
    """Set up services for Fritz integration."""

    for service in [SERVICE_REBOOT, SERVICE_RECONNECT]:
        if opp.services.has_service(DOMAIN, service):
            return

    async def async_call_fritz_service(service_call):
        """Call correct Fritz service."""

        if not (
            fritzbox_entry_ids := await _async_get_configured_fritz_tools(
                opp, service_call
            )
        ):
            raise OpenPeerPowerError(
                f"Failed to call service '{service_call.service}'. Config entry for target not found"
            )

        for entry in fritzbox_entry_ids:
            _LOGGER.debug("Executing service %s", service_call.service)
            fritz_tools = opp.data[DOMAIN][entry]
            await fritz_tools.service_fritzbox(service_call.service)

    for service in [SERVICE_REBOOT, SERVICE_RECONNECT]:
        opp.services.async_register(DOMAIN, service, async_call_fritz_service)


async def _async_get_configured_fritz_tools(
    opp: OpenPeerPower, service_call: ServiceCall
):
    """Get FritzBoxTools class from config entry."""

    list_entry_id = []
    for entry_id in await async_extract_config_entry_ids(opp, service_call):
        config_entry = opp.config_entries.async_get_entry(entry_id)
        if config_entry and config_entry.domain == DOMAIN:
            list_entry_id.append(entry_id)
    return list_entry_id


async def async_unload_services(opp: OpenPeerPower):
    """Unload services for Fritz integration."""

    if not opp.data.get(FRITZ_SERVICES):
        return

    opp.data[FRITZ_SERVICES] = False

    opp.services.async_remove(DOMAIN, SERVICE_REBOOT)
    opp.services.async_remove(DOMAIN, SERVICE_RECONNECT)
