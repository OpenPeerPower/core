"""Helper methods to help with platform discovery.

There are two different types of discoveries that can be fired/listened for.
 - listen/discover is for services. These are targeted at a component.
 - listen_platform/discover_platform is for platforms. These are used by
   components to allow discovery of their platforms.
"""
from typing import Any, Callable, Dict, Optional, TypedDict

from openpeerpower import core, setup
from openpeerpower.core import CALLBACK_TYPE
from openpeerpower.loader import bind_opp

from .dispatcher import async_dispatcher_connect, async_dispatcher_send
from .typing import ConfigType, DiscoveryInfoType

SIGNAL_PLATFORM_DISCOVERED = "discovery.platform_discovered_{}"
EVENT_LOAD_PLATFORM = "load_platform.{}"
ATTR_PLATFORM = "platform"
ATTR_DISCOVERED = "discovered"

# mypy: disallow-any-generics


class DiscoveryDict(TypedDict):
    """Discovery data."""

    service: str
    platform: Optional[str]
    discovered: Optional[DiscoveryInfoType]


@core.callback
@bind_opp
def async_listen(
    opp: core.OpenPeerPower,
    service: str,
    callback: CALLBACK_TYPE,
) -> None:
    """Set up listener for discovery of specific service.

    Service can be a string or a list/tuple.
    """
    job = core.OppJob(callback)

    async def discovery_event_listener(discovered: DiscoveryDict) -> None:
        """Listen for discovery events."""
        task = opp.async_run_opp_job(
            job, discovered["service"], discovered["discovered"]
        )
        if task:
            await task

    async_dispatcher_connect(
        opp, SIGNAL_PLATFORM_DISCOVERED.format(service), discovery_event_listener
    )


@bind_opp
def discover(
    opp: core.OpenPeerPower,
    service: str,
    discovered: DiscoveryInfoType,
    component: str,
    opp_config: ConfigType,
) -> None:
    """Fire discovery event. Can ensure a component is loaded."""
    opp.add_job(
        async_discover(opp, service, discovered, component, opp_config)  # type: ignore
    )


@bind_opp
async def async_discover(
    opp: core.OpenPeerPower,
    service: str,
    discovered: Optional[DiscoveryInfoType],
    component: Optional[str],
    opp_config: ConfigType,
) -> None:
    """Fire discovery event. Can ensure a component is loaded."""
    if component is not None and component not in opp.config.components:
        await setup.async_setup_component(opp, component, opp_config)

    data: DiscoveryDict = {
        "service": service,
        "platform": None,
        "discovered": discovered,
    }

    async_dispatcher_send(opp, SIGNAL_PLATFORM_DISCOVERED.format(service), data)


@bind_opp
def async_listen_platform(
    opp: core.OpenPeerPower,
    component: str,
    callback: Callable[[str, Optional[Dict[str, Any]]], Any],
) -> None:
    """Register a platform loader listener.

    This method must be run in the event loop.
    """
    service = EVENT_LOAD_PLATFORM.format(component)
    job = core.OppJob(callback)

    async def discovery_platform_listener(discovered: DiscoveryDict) -> None:
        """Listen for platform discovery events."""
        platform = discovered["platform"]

        if not platform:
            return

        task = opp.async_run_opp_job(job, platform, discovered.get("discovered"))
        if task:
            await task

    async_dispatcher_connect(
        opp, SIGNAL_PLATFORM_DISCOVERED.format(service), discovery_platform_listener
    )


@bind_opp
def load_platform(
    opp: core.OpenPeerPower,
    component: str,
    platform: str,
    discovered: DiscoveryInfoType,
    opp_config: ConfigType,
) -> None:
    """Load a component and platform dynamically."""
    opp.add_job(
        async_load_platform(  # type: ignore
            opp, component, platform, discovered, opp_config
        )
    )


@bind_opp
async def async_load_platform(
    opp: core.OpenPeerPower,
    component: str,
    platform: str,
    discovered: DiscoveryInfoType,
    opp_config: ConfigType,
) -> None:
    """Load a component and platform dynamically.

    Use `async_listen_platform` to register a callback for these events.

    Warning: Do not await this inside a setup method to avoid a dead lock.
    Use `opp.async_create_task(async_load_platform(..))` instead.
    """
    assert opp_config, "You need to pass in the real opp config"

    setup_success = True

    if component not in opp.config.components:
        setup_success = await setup.async_setup_component(opp, component, opp_config)

    # No need to send signal if we could not set up component
    if not setup_success:
        return

    service = EVENT_LOAD_PLATFORM.format(component)

    data: DiscoveryDict = {
        "service": service,
        "platform": platform,
        "discovered": discovered,
    }

    async_dispatcher_send(opp, SIGNAL_PLATFORM_DISCOVERED.format(service), data)
