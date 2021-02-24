"""The template component."""
from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.helpers.reload import async_reload_integration_platforms

from .const import DOMAIN, EVENT_TEMPLATE_RELOADED, PLATFORMS


async def async_setup_reload_service(opp):
    """Create the reload service for the template domain."""
    if opp.services.has_service(DOMAIN, SERVICE_RELOAD):
        return

    async def _reload_config(call):
        """Reload the template platform config."""
        await async_reload_integration_platforms(opp, DOMAIN, PLATFORMS)
        opp.bus.async_fire(EVENT_TEMPLATE_RELOADED, context=call.context)

    opp.helpers.service.async_register_admin_service(
        DOMAIN, SERVICE_RELOAD, _reload_config
    )
