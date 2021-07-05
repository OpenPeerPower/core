"""The sms component."""

import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_DEVICE
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv

from .const import DOMAIN, SMS_GATEWAY
from .gateway import create_sms_gateway

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.isdevice})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Configure Gammu state machine."""
    opp.data.setdefault(DOMAIN, {})
    sms_config = config.get(DOMAIN, {})
    if not sms_config:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=sms_config,
        )
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Configure Gammu state machine."""

    device = entry.data[CONF_DEVICE]
    config = {"Device": device, "Connection": "at"}
    gateway = await create_sms_gateway(config, opp)
    if not gateway:
        return False
    opp.data[DOMAIN][SMS_GATEWAY] = gateway
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        gateway = opp.data[DOMAIN].pop(SMS_GATEWAY)
        await gateway.terminate_async()

    return unload_ok
