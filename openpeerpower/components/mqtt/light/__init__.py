"""Support for MQTT lights."""
import functools

import voluptuous as vol

from openpeerpower.components import light
from openpeerpower.helpers.reload import async_setup_reload_service
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from .. import DOMAIN, PLATFORMS
from ..mixins import async_setup_entry_helper
from .schema import CONF_SCHEMA, MQTT_LIGHT_SCHEMA_SCHEMA
from .schema_basic import PLATFORM_SCHEMA_BASIC, async_setup_entity_basic
from .schema_json import PLATFORM_SCHEMA_JSON, async_setup_entity_json
from .schema_template import PLATFORM_SCHEMA_TEMPLATE, async_setup_entity_template


def validate_mqtt_light(value):
    """Validate MQTT light schema."""
    schemas = {
        "basic": PLATFORM_SCHEMA_BASIC,
        "json": PLATFORM_SCHEMA_JSON,
        "template": PLATFORM_SCHEMA_TEMPLATE,
    }
    return schemas[value[CONF_SCHEMA]](value)


PLATFORM_SCHEMA = vol.All(
    MQTT_LIGHT_SCHEMA_SCHEMA.extend({}, extra=vol.ALLOW_EXTRA), validate_mqtt_light
)


async def async_setup_platform(
    opp: OpenPeerPowerType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up MQTT light through configuration.yaml."""
    await async_setup_reload_service(opp, DOMAIN, PLATFORMS)
    await _async_setup_entity(opp, async_add_entities, config)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up MQTT light dynamically through MQTT discovery."""
    setup = functools.partial(
        _async_setup_entity, opp, async_add_entities, config_entry=config_entry
    )
    await async_setup_entry_helper(opp, light.DOMAIN, setup, PLATFORM_SCHEMA)


async def _async_setup_entity(
    opp, async_add_entities, config, config_entry=None, discovery_data=None
):
    """Set up a MQTT Light."""
    setup_entity = {
        "basic": async_setup_entity_basic,
        "json": async_setup_entity_json,
        "template": async_setup_entity_template,
    }
    await setup_entity[config[CONF_SCHEMA]](
        opp, config, async_add_entities, config_entry, discovery_data
    )
