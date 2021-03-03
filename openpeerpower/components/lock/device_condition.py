"""Provides device automations for Lock."""
from typing import List

import voluptuous as vol

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    STATE_LOCKED,
    STATE_UNLOCKED,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import condition, config_validation as cv, entity_registry
from openpeerpower.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from openpeerpower.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

CONDITION_TYPES = {"is_locked", "is_unlocked"}

CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES),
    }
)


async def async_get_conditions(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device conditions for Lock devices."""
    registry = await entity_registry.async_get_registry(opp)
    conditions = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        # Add conditions for each entity that belongs to this integration
        conditions.append(
            {
                CONF_CONDITION: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "is_locked",
            }
        )
        conditions.append(
            {
                CONF_CONDITION: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "is_unlocked",
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
    if config[CONF_TYPE] == "is_locked":
        state = STATE_LOCKED
    else:
        state = STATE_UNLOCKED

    def test_is_state(opp: OpenPeerPower, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return condition.state(opp, config[ATTR_ENTITY_ID], state)

    return test_is_state
