"""Provides device automations for Cover."""
from typing import Any, Dict, List

import voluptuous as vol

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    CONF_ABOVE,
    CONF_BELOW,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import (
    condition,
    config_validation as cv,
    entity_registry,
    template,
)
from openpeerpower.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from openpeerpower.helpers.typing import ConfigType, TemplateVarsType

from . import (
    DOMAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
)

POSITION_CONDITION_TYPES = {"is_position", "is_tilt_position"}
STATE_CONDITION_TYPES = {"is_open", "is_closed", "is_opening", "is_closing"}

POSITION_CONDITION_SCHEMA = vol.All(
    DEVICE_CONDITION_BASE_SCHEMA.extend(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In(POSITION_CONDITION_TYPES),
            vol.Optional(CONF_ABOVE): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional(CONF_BELOW): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
        }
    ),
    cv.has_at_least_one_key(CONF_BELOW, CONF_ABOVE),
)

STATE_CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(STATE_CONDITION_TYPES),
    }
)

CONDITION_SCHEMA = vol.Any(POSITION_CONDITION_SCHEMA, STATE_CONDITION_SCHEMA)


async def async_get_conditions(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device conditions for Cover devices."""
    registry = await entity_registry.async_get_registry(opp)
    conditions: List[Dict[str, Any]] = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = opp.states.get(entry.entity_id)
        if not state or ATTR_SUPPORTED_FEATURES not in state.attributes:
            continue

        supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
        supports_open_close = supported_features & (SUPPORT_OPEN | SUPPORT_CLOSE)

        # Add conditions for each entity that belongs to this integration
        if supports_open_close:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_open",
                }
            )
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_closed",
                }
            )
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_opening",
                }
            )
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_closing",
                }
            )
        if supported_features & SUPPORT_SET_POSITION:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_position",
                }
            )
        if supported_features & SUPPORT_SET_TILT_POSITION:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_tilt_position",
                }
            )

    return conditions


async def async_get_condition_capabilities(opp: OpenPeerPower, config: dict) -> dict:
    """List condition capabilities."""
    if config[CONF_TYPE] not in ["is_position", "is_tilt_position"]:
        return {}

    return {
        "extra_fields": vol.Schema(
            {
                vol.Optional(CONF_ABOVE, default=0): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=100)
                ),
                vol.Optional(CONF_BELOW, default=100): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=100)
                ),
            }
        )
    }


@callback
def async_condition_from_config(
    config: ConfigType, config_validation: bool
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config_validation:
        config = CONDITION_SCHEMA(config)

    if config[CONF_TYPE] in STATE_CONDITION_TYPES:
        if config[CONF_TYPE] == "is_open":
            state = STATE_OPEN
        elif config[CONF_TYPE] == "is_closed":
            state = STATE_CLOSED
        elif config[CONF_TYPE] == "is_opening":
            state = STATE_OPENING
        elif config[CONF_TYPE] == "is_closing":
            state = STATE_CLOSING

        def test_is_state(opp: OpenPeerPower, variables: TemplateVarsType) -> bool:
            """Test if an entity is a certain state."""
            return condition.state(opp, config[ATTR_ENTITY_ID], state)

        return test_is_state

    if config[CONF_TYPE] == "is_position":
        position = "current_position"
    if config[CONF_TYPE] == "is_tilt_position":
        position = "current_tilt_position"
    min_pos = config.get(CONF_ABOVE)
    max_pos = config.get(CONF_BELOW)
    value_template = template.Template(  # type: ignore
        f"{{{{ state.attributes.{position} }}}}"
    )

    @callback
    def template_if(opp: OpenPeerPower, variables: TemplateVarsType = None) -> bool:
        """Validate template based if-condition."""
        value_template.opp = opp

        return condition.async_numeric_state(
            opp, config[ATTR_ENTITY_ID], max_pos, min_pos, value_template
        )

    return template_if
