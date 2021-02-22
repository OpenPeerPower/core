"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
import asyncio
import logging

import voluptuous as vol

from openpeerpower.components.discovery import SERVICE_FREEBOX
from openpeerpower.config_entries import SOURCE_DISCOVERY, SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT, EVENT_OPENPEERPOWER_STOP
from openpeerpower.helpers import config_validation as cv, discovery
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import DOMAIN, PLATFORMS
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)

FREEBOX_SCHEMA = vol.Schema(
    {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_PORT): cv.port}
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [FREEBOX_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Freebox component."""
    conf = config.get(DOMAIN)

    async def discovery_dispatch(service, discovery_info):
        if conf is None:
            host = discovery_info.get("properties", {}).get("api_domain")
            port = discovery_info.get("properties", {}).get("https_port")
            _LOGGER.info("Discovered Freebox server: %s:%s", host, port)
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_DISCOVERY},
                    data={CONF_HOST: host, CONF_PORT: port},
                )
            )

    discovery.async_listen.opp, SERVICE_FREEBOX, discovery_dispatch)

    if conf is None:
        return True

    for freebox_conf in conf:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=freebox_conf,
            )
        )

    return True


async def async_setup_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Set up Freebox component."""
    router = FreeboxRouter.opp, entry)
    await router.setup()

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.unique_id] = router

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    # Services
    async def async_reboot(call):
        """Handle reboot service call."""
        await router.reboot()

    opp.services.async_register(DOMAIN, "reboot", async_reboot)

    async def async_close_connection(event):
        """Close Freebox connection on HA Stop."""
        await router.close()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, async_close_connection)

    return True


async def async_unload_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        router = opp.data[DOMAIN].pop(entry.unique_id)
        await router.close()

    return unload_ok
