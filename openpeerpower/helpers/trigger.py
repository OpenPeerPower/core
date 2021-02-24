"""Triggers."""
import asyncio
import logging
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Optional, Union

import voluptuous as vol

from openpeerpower.const import CONF_PLATFORM
from openpeerpower.core import CALLBACK_TYPE, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.loader import IntegrationNotFound, async_get_integration

_PLATFORM_ALIASES = {
    "device_automation": ("device",),
    "openpeerpower": ("event", "numeric_state", "state", "time_pattern", "time"),
}


async def _async_get_trigger_platform(
    opp: OpenPeerPowerType, config: ConfigType
) -> Any:
    platform = config[CONF_PLATFORM]
    for alias, triggers in _PLATFORM_ALIASES.items():
        if platform in triggers:
            platform = alias
            break
    try:
        integration = await async_get_integration(opp, platform)
    except IntegrationNotFound:
        raise vol.Invalid(f"Invalid platform '{platform}' specified") from None
    try:
        return integration.get_platform("trigger")
    except ImportError:
        raise vol.Invalid(
            f"Integration '{platform}' does not provide trigger support"
        ) from None


async def async_validate_trigger_config(
    opp: OpenPeerPowerType, trigger_config: List[ConfigType]
) -> List[ConfigType]:
    """Validate triggers."""
    config = []
    for conf in trigger_config:
        platform = await _async_get_trigger_platform(opp, conf)
        if hasattr(platform, "async_validate_trigger_config"):
            conf = await platform.async_validate_trigger_config(opp, conf)
        else:
            conf = platform.TRIGGER_SCHEMA(conf)
        config.append(conf)
    return config


async def async_initialize_triggers(
    opp: OpenPeerPowerType,
    trigger_config: List[ConfigType],
    action: Callable,
    domain: str,
    name: str,
    log_cb: Callable,
    open_peer_power_start: bool = False,
    variables: Optional[Union[Dict[str, Any], MappingProxyType]] = None,
) -> Optional[CALLBACK_TYPE]:
    """Initialize triggers."""
    info = {
        "domain": domain,
        "name": name,
        "open_peer_power_start": open_peer_power_start,
        "variables": variables,
    }

    triggers = []
    for conf in trigger_config:
        platform = await _async_get_trigger_platform(opp, conf)
        triggers.append(platform.async_attach_trigger(opp, conf, action, info))

    attach_results = await asyncio.gather(*triggers, return_exceptions=True)
    removes = []

    for result in attach_results:
        if isinstance(result, OpenPeerPowerError):
            log_cb(logging.ERROR, f"Got error '{result}' when setting up triggers for")
        elif isinstance(result, Exception):
            log_cb(logging.ERROR, "Error setting up trigger", exc_info=result)
        elif result is None:
            log_cb(
                logging.ERROR, "Unknown error while setting up trigger (empty result)"
            )
        else:
            removes.append(result)

    if not removes:
        return None

    log_cb(logging.INFO, "Initialized trigger")

    @callback
    def remove_triggers():  # type: ignore
        """Remove triggers."""
        for remove in removes:
            remove()

    return remove_triggers
