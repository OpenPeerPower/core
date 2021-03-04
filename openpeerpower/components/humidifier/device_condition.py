"""Provide the device automations for Humidifier."""
from typing import Dict, List

import voluptuous as vol

from openpeerpower.components.device_automation import toggle_entity
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    ATTR_SUPPORTED_FEATURES,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import condition, config_validation as cv, entity_registry
from openpeerpower.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from openpeerpower.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN, const

TOGGLE_CONDITION = toggle_entity.CONDITION_SCHEMA.extend(
    {vol.Required(CONF_DOMAIN): DOMAIN}
)

MODE_CONDITION = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): "is_mode",
        vol.Required(ATTR_MODE): str,
    }
)

CONDITION_SCHEMA = vol.Any(TOGGLE_CONDITION, MODE_CONDITION)


async def async_get_conditions(
    opp: OpenPeerPower, device_id: str
) -> List[Dict[str, str]]:
    """List device conditions for Humidifier devices."""
    registry = await entity_registry.async_get_registry(opp)
    conditions = await toggle_entity.async_get_conditions(opp, device_id, DOMAIN)

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = opp.states.get(entry.entity_id)

        if state and state.attributes[ATTR_SUPPORTED_FEATURES] & const.SUPPORT_MODES:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_mode",
                }
            )

    return conditions


@callback
def async_condition_from_config(
    config: ConfigType, config_validation: bool
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config_validation:
        config = CONDITION_SCHEMA(config)

    if config[CONF_TYPE] == "is_mode":
        attribute = ATTR_MODE
    else:
        return toggle_entity.async_condition_from_config(config)

    def test_is_state(opp: OpenPeerPower, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        state = opp.states.get(config[ATTR_ENTITY_ID])
        return state and state.attributes.get(attribute) == config[attribute]

    return test_is_state


async def async_get_condition_capabilities(opp, config):
    """List condition capabilities."""
    state = opp.states.get(config[CONF_ENTITY_ID])
    condition_type = config[CONF_TYPE]

    fields = {}

    if condition_type == "is_mode":
        if state:
            modes = state.attributes.get(const.ATTR_AVAILABLE_MODES, [])
        else:
            modes = []

        fields[vol.Required(const.ATTR_AVAILABLE_MODES)] = vol.In(modes)

        return {"extra_fields": vol.Schema(fields)}

    return await toggle_entity.async_get_condition_capabilities(opp, config)
