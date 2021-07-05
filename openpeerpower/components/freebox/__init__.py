"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
import logging

import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, SERVICE_REBOOT
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)

FREEBOX_SCHEMA = vol.Schema(
    {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_PORT): cv.port}
)

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [FREEBOX_SCHEMA]))},
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Freebox integration."""
    if DOMAIN in config:
        for entry_config in config[DOMAIN]:
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=entry_config
                )
            )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Freebox entry."""
    router = FreeboxRouter(opp, entry)
    await router.setup()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.unique_id] = router

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    # Services
    async def async_reboot(call):
        """Handle reboot service call."""
        await router.reboot()

    opp.services.async_register(DOMAIN, SERVICE_REBOOT, async_reboot)

    async def async_close_connection(event):
        """Close Freebox connection on OPP Stop."""
        await router.close()

    entry.async_on_unload(
        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, async_close_connection)
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        router = opp.data[DOMAIN].pop(entry.unique_id)
        await router.close()
        opp.services.async_remove(DOMAIN, SERVICE_REBOOT)

    return unload_ok
