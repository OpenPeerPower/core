"""Provide the device automations for Fan."""
from typing import Dict, List

import voluptuous as vol

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import condition, config_validation as cv, entity_registry
from openpeerpower.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from openpeerpower.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

CONDITION_TYPES = {"is_on", "is_off"}

CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES),
    }
)


async def async_get_conditions(
    opp: OpenPeerPower, device_id: str
) -> List[Dict[str, str]]:
    """List device conditions for Fan devices."""
    registry = await entity_registry.async_get_registry(opp)
    conditions = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        conditions.append(
            {
                CONF_CONDITION: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "is_on",
            }
        )
        conditions.append(
            {
                CONF_CONDITION: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "is_off",
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
    if config[CONF_TYPE] == "is_on":
        state = STATE_ON
    else:
        state = STATE_OFF

    @callback
    def test_is_state(opp: OpenPeerPower, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return condition.state(opp, config[ATTR_ENTITY_ID], state)

    return test_is_state
