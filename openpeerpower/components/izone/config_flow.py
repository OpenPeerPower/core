"""Config flow for izone."""

import asyncio
from contextlib import suppress
import logging

from async_timeout import timeout

from openpeerpower.core import callback
from openpeerpower.helpers import config_entry_flow
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import DISPATCH_CONTROLLER_DISCOVERED, IZONE, TIMEOUT_DISCOVERY
from .discovery import async_start_discovery_service, async_stop_discovery_service

_LOGGER = logging.getLogger(__name__)


async def _async_has_devices(opp):

    controller_ready = asyncio.Event()

    @callback
    def dispatch_discovered(_):
        controller_ready.set()

    async_dispatcher_connect(opp, DISPATCH_CONTROLLER_DISCOVERED, dispatch_discovered)

    disco = await async_start_discovery_service(opp)

    with suppress(asyncio.TimeoutError):
        async with timeout(TIMEOUT_DISCOVERY):
            await controller_ready.wait()

    if not disco.pi_disco.controllers:
        await async_stop_discovery_service(opp)
        _LOGGER.debug("No controllers found")
        return False

    _LOGGER.debug("Controllers %s", disco.pi_disco.controllers)
    return True


config_entry_flow.register_discovery_flow(IZONE, "iZone Aircon", _async_has_devices)
