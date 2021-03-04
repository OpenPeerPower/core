"""Helpers to help with integration platforms."""
import asyncio
import logging
from typing import Any, Awaitable, Callable

from openpeerpower.core import Event, OpenPeerPower
from openpeerpower.loader import async_get_integration, bind_opp
from openpeerpower.setup import ATTR_COMPONENT, EVENT_COMPONENT_LOADED

_LOGGER = logging.getLogger(__name__)


@bind_opp
async def async_process_integration_platforms(
    opp: OpenPeerPower,
    platform_name: str,
    # Any = platform.
    process_platform: Callable[[OpenPeerPower, str, Any], Awaitable[None]],
) -> None:
    """Process a specific platform for all current and future loaded integrations."""

    async def _process(component_name: str) -> None:
        """Process the intents of a component."""
        if "." in component_name:
            return

        integration = await async_get_integration(opp, component_name)

        try:
            platform = integration.get_platform(platform_name)
        except ImportError as err:
            if f"{component_name}.{platform_name}" not in str(err):
                _LOGGER.exception(
                    "Unexpected error importing %s/%s.py",
                    component_name,
                    platform_name,
                )
            return

        try:
            await process_platform(opp, component_name, platform)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Error processing platform %s.%s", component_name, platform_name
            )

    async def async_component_loaded(event: Event) -> None:
        """Handle a new component loaded."""
        await _process(event.data[ATTR_COMPONENT])

    opp.bus.async_listen(EVENT_COMPONENT_LOADED, async_component_loaded)

    tasks = [_process(comp) for comp in opp.config.components]

    if tasks:
        await asyncio.gather(*tasks)
