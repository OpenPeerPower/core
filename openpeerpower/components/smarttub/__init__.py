"""SmartTub integration."""
import asyncio
import logging

from .const import DOMAIN, SMARTTUB_CONTROLLER
from .controller import SmartTubController

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "climate", "light", "sensor", "switch"]


async def async_setup(opp, config):
    """Set up smarttub component."""

    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp, entry):
    """Set up a smarttub config entry."""

    controller = SmartTubController(opp)
    opp.data[DOMAIN][entry.entry_id] = {
        SMARTTUB_CONTROLLER: controller,
    }

    if not await controller.async_setup_entry(entry):
        return False

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp, entry):
    """Remove a smarttub config entry."""
    if not all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    ):
        return False

    opp.data[DOMAIN].pop(entry.entry_id)

    return True
