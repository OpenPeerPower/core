"""SmartTub integration."""
import logging

from .const import DOMAIN, SMARTTUB_CONTROLLER
from .controller import SmartTubController

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "climate", "light", "sensor", "switch"]


async def async_setup_entry(opp, entry):
    """Set up a smarttub config entry."""

    controller = SmartTubController(opp)
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        SMARTTUB_CONTROLLER: controller,
    }

    if not await controller.async_setup_entry(entry):
        return False

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp, entry):
    """Remove a smarttub config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
