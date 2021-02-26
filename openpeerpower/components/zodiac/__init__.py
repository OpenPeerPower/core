"""The zodiac component."""
import voluptuous as vol

from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.discovery import async_load_platform

from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(DOMAIN): {}},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the zodiac component."""
    opp.async_create_task(async_load_platform(opp, "sensor", DOMAIN, {}, config))

    return True
