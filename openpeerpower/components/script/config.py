"""Config validation helper for the script integration."""
import asyncio

import voluptuous as vol

from openpeerpower.config import async_log_exception
from openpeerpower.const import CONF_SEQUENCE
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.script import async_validate_action_config

from . import DOMAIN, SCRIPT_ENTRY_SCHEMA


async def async_validate_config_item(opp, config, full_config=None):
    """Validate config item."""
    config = SCRIPT_ENTRY_SCHEMA(config)
    config[CONF_SEQUENCE] = await asyncio.gather(
        *[async_validate_action_config(opp, action) for action in config[CONF_SEQUENCE]]
    )

    return config


async def _try_async_validate_config_item(opp, object_id, config, full_config=None):
    """Validate config item."""
    try:
        cv.slug(object_id)
        config = await async_validate_config_item(opp, config, full_config)
    except (vol.Invalid, OpenPeerPowerError) as ex:
        async_log_exception(ex, DOMAIN, full_config or config, opp)
        return None

    return config


async def async_validate_config(opp, config):
    """Validate config."""
    if DOMAIN in config:
        validated_config = {}
        for object_id, cfg in config[DOMAIN].items():
            cfg = await _try_async_validate_config_item(opp, object_id, cfg, config)
            if cfg is not None:
                validated_config[object_id] = cfg
        config[DOMAIN] = validated_config

    return config
