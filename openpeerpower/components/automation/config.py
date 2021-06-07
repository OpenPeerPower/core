"""Config validation helper for the automation integration."""
import asyncio
from contextlib import suppress

import voluptuous as vol

from openpeerpower.components import blueprint
from openpeerpower.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from openpeerpower.components.trace import TRACE_CONFIG_SCHEMA
from openpeerpower.config import async_log_exception, config_without_domain
from openpeerpower.const import (
    CONF_ALIAS,
    CONF_CONDITION,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_VARIABLES,
)
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_per_platform, config_validation as cv, script
from openpeerpower.helpers.condition import async_validate_condition_config
from openpeerpower.helpers.trigger import async_validate_trigger_config
from openpeerpower.loader import IntegrationNotFound

from .const import (
    CONF_ACTION,
    CONF_HIDE_ENTITY,
    CONF_INITIAL_STATE,
    CONF_TRACE,
    CONF_TRIGGER,
    CONF_TRIGGER_VARIABLES,
    DOMAIN,
)
from .helpers import async_get_blueprints

# mypy: allow-untyped-calls, allow-untyped-defs
# mypy: no-check-untyped-defs, no-warn-return-any

_CONDITION_SCHEMA = vol.All(cv.ensure_list, [cv.CONDITION_SCHEMA])

PLATFORM_SCHEMA = vol.All(
    cv.deprecated(CONF_HIDE_ENTITY),
    script.make_script_schema(
        {
            # str on purpose
            CONF_ID: str,
            CONF_ALIAS: cv.string,
            vol.Optional(CONF_DESCRIPTION): cv.string,
            vol.Optional(CONF_TRACE, default={}): TRACE_CONFIG_SCHEMA,
            vol.Optional(CONF_INITIAL_STATE): cv.boolean,
            vol.Optional(CONF_HIDE_ENTITY): cv.boolean,
            vol.Required(CONF_TRIGGER): cv.TRIGGER_SCHEMA,
            vol.Optional(CONF_CONDITION): _CONDITION_SCHEMA,
            vol.Optional(CONF_VARIABLES): cv.SCRIPT_VARIABLES_SCHEMA,
            vol.Optional(CONF_TRIGGER_VARIABLES): cv.SCRIPT_VARIABLES_SCHEMA,
            vol.Required(CONF_ACTION): cv.SCRIPT_SCHEMA,
        },
        script.SCRIPT_MODE_SINGLE,
    ),
)


async def async_validate_config_item(opp, config, full_config=None):
    """Validate config item."""
    if blueprint.is_blueprint_instance_config(config):
        blueprints = async_get_blueprints(opp)
        return await blueprints.async_inputs_from_config(config)

    config = PLATFORM_SCHEMA(config)

    config[CONF_TRIGGER] = await async_validate_trigger_config(
        opp, config[CONF_TRIGGER]
    )

    if CONF_CONDITION in config:
        config[CONF_CONDITION] = await asyncio.gather(
            *[
                async_validate_condition_config(opp, cond)
                for cond in config[CONF_CONDITION]
            ]
        )

    config[CONF_ACTION] = await script.async_validate_actions_config(
        opp, config[CONF_ACTION]
    )

    return config


class AutomationConfig(dict):
    """Dummy class to allow adding attributes."""

    raw_config = None


async def _try_async_validate_config_item(opp, config, full_config=None):
    """Validate config item."""
    raw_config = None
    with suppress(ValueError):
        raw_config = dict(config)

    try:
        config = await async_validate_config_item(opp, config, full_config)
    except (
        vol.Invalid,
        OpenPeerPowerError,
        IntegrationNotFound,
        InvalidDeviceAutomationConfig,
    ) as ex:
        async_log_exception(ex, DOMAIN, full_config or config, opp)
        return None

    if isinstance(config, blueprint.BlueprintInputs):
        return config

    config = AutomationConfig(config)
    config.raw_config = raw_config
    return config


async def async_validate_config(opp, config):
    """Validate config."""
    automations = list(
        filter(
            lambda x: x is not None,
            await asyncio.gather(
                *(
                    _try_async_validate_config_item(opp, p_config, config)
                    for _, p_config in config_per_platform(config, DOMAIN)
                )
            ),
        )
    )

    # Create a copy of the configuration with all config for current
    # component removed and add validated config back in.
    config = config_without_domain(config, DOMAIN)
    config[DOMAIN] = automations

    return config
