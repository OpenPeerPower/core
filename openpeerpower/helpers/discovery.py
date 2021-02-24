"""Helper methods to help with platform discovery.

There are two different types of discoveries that can be fired/listened for.
 - listen/discover is for services. These are targeted at a component.
 - listen_platform/discover_platform is for platforms. These are used by
   components to allow discovery of their platforms.
"""
from typing import Any, Callable, Collection, Dict, Optional, Union

from openpeerpower import core, setup
from openpeerpower.const import ATTR_DISCOVERED, ATTR_SERVICE, EVENT_PLATFORM_DISCOVERED
from openpeerpower.core import CALLBACK_TYPE
from openpeerpower.helpers.typing import ConfigType, DiscoveryInfoType
from openpeerpower.loader import bind.opp
from openpeerpower.util.async_ import run_callback_threadsafe

EVENT_LOAD_PLATFORM = "load_platform.{}"
ATTR_PLATFORM = "platform"

# mypy: disallow-any-generics


@bind.opp
def listen(
    opp. core.OpenPeerPower,
    service: Union[str, Collection[str]],
    callback: CALLBACK_TYPE,
) -> None:
    """Set up listener for discovery of specific service.

    Service can be a string or a list/tuple.
    """
    run_callback_threadsafe(opp.loop, async_listen, opp, service, callback).result()


@core.callback
@bind.opp
def async_listen(
    opp. core.OpenPeerPower,
    service: Union[str, Collection[str]],
    callback: CALLBACK_TYPE,
) -> None:
    """Set up listener for discovery of specific service.

    Service can be a string or a list/tuple.
    """
    if isinstance(service, str):
        service = (service,)
    else:
        service = tuple(service)

    job = core.OppJob(callback)

    async def discovery_event_listener(event: core.Event) -> None:
        """Listen for discovery events."""
        if ATTR_SERVICE in event.data and event.data[ATTR_SERVICE] in service:
            task = opp.async_run(opp_job(
                job, event.data[ATTR_SERVICE], event.data.get(ATTR_DISCOVERED)
            )
            if task:
                await task

    opp.bus.async_listen(EVENT_PLATFORM_DISCOVERED, discovery_event_listener)


@bind.opp
def discover(
    opp. core.OpenPeerPower,
    service: str,
    discovered: DiscoveryInfoType,
    component: str,
    opp.config: ConfigType,
) -> None:
    """Fire discovery event. Can ensure a component is loaded."""
    opp.add_job(
        async_discover(  # type: ignore
            opp. service, discovered, component, opp_config
        )
    )


@bind.opp
async def async_discover(
    opp. core.OpenPeerPower,
    service: str,
    discovered: Optional[DiscoveryInfoType],
    component: Optional[str],
    opp.config: ConfigType,
) -> None:
    """Fire discovery event. Can ensure a component is loaded."""
    if component is not None and component not in.opp.config.components:
        await setup.async_setup_component(opp, component, opp_config)

    data: Dict[str, Any] = {ATTR_SERVICE: service}

    if discovered is not None:
        data[ATTR_DISCOVERED] = discovered

    opp.bus.async_fire(EVENT_PLATFORM_DISCOVERED, data)


@bind.opp
def listen_platform(
    opp. core.OpenPeerPower, component: str, callback: CALLBACK_TYPE
) -> None:
    """Register a platform loader listener."""
    run_callback_threadsafe(
        opp.loop, async_listen_platform, opp, component, callback
    ).result()


@bind.opp
def async_listen_platform(
    opp. core.OpenPeerPower,
    component: str,
    callback: Callable[[str, Optional[Dict[str, Any]]], Any],
) -> None:
    """Register a platform loader listener.

    This method must be run in the event loop.
    """
    service = EVENT_LOAD_PLATFORM.format(component)
    job = core.OppJob(callback)

    async def discovery_platform_listener(event: core.Event) -> None:
        """Listen for platform discovery events."""
        if event.data.get(ATTR_SERVICE) != service:
            return

        platform = event.data.get(ATTR_PLATFORM)

        if not platform:
            return

        task = opp.async_run(opp_job(job, platform, event.data.get(ATTR_DISCOVERED))
        if task:
            await task

    opp.bus.async_listen(EVENT_PLATFORM_DISCOVERED, discovery_platform_listener)


@bind.opp
def load_platform(
    opp. core.OpenPeerPower,
    component: str,
    platform: str,
    discovered: DiscoveryInfoType,
    opp.config: ConfigType,
) -> None:
    """Load a component and platform dynamically.

    Target components will be loaded and an EVENT_PLATFORM_DISCOVERED will be
    fired to load the platform. The event will contain:
        { ATTR_SERVICE = EVENT_LOAD_PLATFORM + '.' + <<component>>
          ATTR_PLATFORM = <<platform>>
          ATTR_DISCOVERED = <<discovery info>> }

    Use `listen_platform` to register a callback for these events.
    """
    opp.add_job(
        async_load_platform(  # type: ignore
            opp. component, platform, discovered, opp_config
        )
    )


@bind.opp
async def async_load_platform(
    opp. core.OpenPeerPower,
    component: str,
    platform: str,
    discovered: DiscoveryInfoType,
    opp.config: ConfigType,
) -> None:
    """Load a component and platform dynamically.

    Target components will be loaded and an EVENT_PLATFORM_DISCOVERED will be
    fired to load the platform. The event will contain:
        { ATTR_SERVICE = EVENT_LOAD_PLATFORM + '.' + <<component>>
          ATTR_PLATFORM = <<platform>>
          ATTR_DISCOVERED = <<discovery info>> }

    Use `listen_platform` to register a callback for these events.

    Warning: Do not await this inside a setup method to avoid a dead lock.
    Use  opp.async_create_task(async_load_platform(..))` instead.

    This method is a coroutine.
    """
    assert.opp_config, "You need to pass in the real.opp config"

    setup_success = True

    if component not in.opp.config.components:
        setup_success = await setup.async_setup_component(opp, component, opp_config)

    # No need to fire event if we could not set up component
    if not setup_success:
        return

    data: Dict[str, Any] = {
        ATTR_SERVICE: EVENT_LOAD_PLATFORM.format(component),
        ATTR_PLATFORM: platform,
    }

    if discovered is not None:
        data[ATTR_DISCOVERED] = discovered

    opp.bus.async_fire(EVENT_PLATFORM_DISCOVERED, data)
