"""Class to reload platforms."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging

from openpeerpower import config as conf_util
from openpeerpower.const import SERVICE_RELOAD
from openpeerpower.core import Event, OpenPeerPower, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_per_platform
from openpeerpower.helpers.entity_platform import EntityPlatform, async_get_platforms
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import async_get_integration
from openpeerpower.setup import async_setup_component

_LOGGER = logging.getLogger(__name__)


async def async_reload_integration_platforms(
    opp: OpenPeerPower, integration_name: str, integration_platforms: Iterable
) -> None:
    """Reload an integration's platforms.

    The platform must support being re-setup.

    This functionality is only intended to be used for integrations that process
    Open Peer Power data and make this available to other integrations.

    Examples are template, stats, derivative, utility meter.
    """
    try:
        unprocessed_conf = await conf_util.async_opp_config_yaml(opp)
    except OpenPeerPowerError as err:
        _LOGGER.error(err)
        return

    tasks = [
        _resetup_platform(opp, integration_name, integration_platform, unprocessed_conf)
        for integration_platform in integration_platforms
    ]

    await asyncio.gather(*tasks)


async def _resetup_platform(
    opp: OpenPeerPower,
    integration_name: str,
    integration_platform: str,
    unprocessed_conf: ConfigType,
) -> None:
    """Resetup a platform."""
    integration = await async_get_integration(opp, integration_platform)

    conf = await conf_util.async_process_component_config(
        opp, unprocessed_conf, integration
    )

    if not conf:
        return

    root_config: dict = {integration_platform: []}
    # Extract only the config for template, ignore the rest.
    for p_type, p_config in config_per_platform(conf, integration_platform):
        if p_type != integration_name:
            continue

        root_config[integration_platform].append(p_config)

    component = integration.get_component()

    if hasattr(component, "async_reset_platform"):
        # If the integration has its own way to reset
        # use this method.
        await component.async_reset_platform(opp, integration_name)  # type: ignore
        await component.async_setup(opp, root_config)  # type: ignore
        return

    # If its an entity platform, we use the entity_platform
    # async_reset method
    platform = async_get_platform_without_config_entry(
        opp, integration_name, integration_platform
    )
    if platform:
        await _async_reconfig_platform(platform, root_config[integration_platform])
        return

    if not root_config[integration_platform]:
        # No config for this platform
        # and its not loaded.  Nothing to do
        return

    await _async_setup_platform(
        opp, integration_name, integration_platform, root_config[integration_platform]
    )


async def _async_setup_platform(
    opp: OpenPeerPower,
    integration_name: str,
    integration_platform: str,
    platform_configs: list[dict],
) -> None:
    """Platform for the first time when new configuration is added."""
    if integration_platform not in opp.data:
        await async_setup_component(
            opp, integration_platform, {integration_platform: platform_configs}
        )
        return

    entity_component = opp.data[integration_platform]
    tasks = [
        entity_component.async_setup_platform(integration_name, p_config)
        for p_config in platform_configs
    ]
    await asyncio.gather(*tasks)


async def _async_reconfig_platform(
    platform: EntityPlatform, platform_configs: list[dict]
) -> None:
    """Reconfigure an already loaded platform."""
    await platform.async_reset()
    tasks = [platform.async_setup(p_config) for p_config in platform_configs]
    await asyncio.gather(*tasks)


async def async_integration_yaml_config(
    opp: OpenPeerPower, integration_name: str
) -> ConfigType | None:
    """Fetch the latest yaml configuration for an integration."""
    integration = await async_get_integration(opp, integration_name)

    return await conf_util.async_process_component_config(
        opp, await conf_util.async_opp_config_yaml(opp), integration
    )


@callback
def async_get_platform_without_config_entry(
    opp: OpenPeerPower, integration_name: str, integration_platform_name: str
) -> EntityPlatform | None:
    """Find an existing platform that is not a config entry."""
    for integration_platform in async_get_platforms(opp, integration_name):
        if integration_platform.config_entry is not None:
            continue
        if integration_platform.domain == integration_platform_name:
            platform: EntityPlatform = integration_platform
            return platform

    return None


async def async_setup_reload_service(
    opp: OpenPeerPower, domain: str, platforms: Iterable
) -> None:
    """Create the reload service for the domain."""
    if opp.services.has_service(domain, SERVICE_RELOAD):
        return

    async def _reload_config(call: Event) -> None:
        """Reload the platforms."""
        await async_reload_integration_platforms(opp, domain, platforms)
        opp.bus.async_fire(f"event_{domain}_reloaded", context=call.context)

    opp.helpers.service.async_register_admin_service(
        domain, SERVICE_RELOAD, _reload_config
    )


def setup_reload_service(opp: OpenPeerPower, domain: str, platforms: Iterable) -> None:
    """Sync version of async_setup_reload_service."""
    asyncio.run_coroutine_threadsafe(
        async_setup_reload_service(opp, domain, platforms),
        opp.loop,
    ).result()
