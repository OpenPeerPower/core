"""Provides device automations for Cover."""
from typing import List

import voluptuous as vol

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.components.openpeerpower.triggers import (
    numeric_state as numeric_state_trigger,
    state as state_trigger,
)
from openpeerpower.const import (
    ATTR_SUPPORTED_FEATURES,
    CONF_ABOVE,
    CONF_BELOW,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
    CONF_VALUE_TEMPLATE,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from openpeerpower.core import CALLBACK_TYPE, OpenPeerPower
from openpeerpower.helpers import config_validation as cv, entity_registry
from openpeerpower.helpers.typing import ConfigType

from . import (
    DOMAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
)

POSITION_TRIGGER_TYPES = {"position", "tilt_position"}
STATE_TRIGGER_TYPES = {"opened", "closed", "opening", "closing"}

POSITION_TRIGGER_SCHEMA = vol.All(
    TRIGGER_BASE_SCHEMA.extend(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In(POSITION_TRIGGER_TYPES),
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

STATE_TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(STATE_TRIGGER_TYPES),
    }
)

TRIGGER_SCHEMA = vol.Any(POSITION_TRIGGER_SCHEMA, STATE_TRIGGER_SCHEMA)


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device triggers for Cover devices."""
    registry = await entity_registry.async_get_registry(opp)
    triggers = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = opp.states.get(entry.entity_id)
        if not state or ATTR_SUPPORTED_FEATURES not in state.attributes:
            continue

        supported_features = state.attributes[ATTR_SUPPORTED_FEATURES]
        supports_open_close = supported_features & (SUPPORT_OPEN | SUPPORT_CLOSE)

        # Add triggers for each entity that belongs to this integration
        if supports_open_close:
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "opened",
                }
            )
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "closed",
                }
            )
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "opening",
                }
            )
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "closing",
                }
            )
        if supported_features & SUPPORT_SET_POSITION:
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "position",
                }
            )
        if supported_features & SUPPORT_SET_TILT_POSITION:
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "tilt_position",
                }
            )

    return triggers


async def async_get_trigger_capabilities(opp: OpenPeerPower, config: dict) -> dict:
    """List trigger capabilities."""
    if config[CONF_TYPE] not in ["position", "tilt_position"]:
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


async def async_attach_trigger(
    opp: OpenPeerPower,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    config = TRIGGER_SCHEMA(config)

    if config[CONF_TYPE] in STATE_TRIGGER_TYPES:
        if config[CONF_TYPE] == "opened":
            to_state = STATE_OPEN
        elif config[CONF_TYPE] == "closed":
            to_state = STATE_CLOSED
        elif config[CONF_TYPE] == "opening":
            to_state = STATE_OPENING
        elif config[CONF_TYPE] == "closing":
            to_state = STATE_CLOSING

        state_config = {
            CONF_PLATFORM: "state",
            CONF_ENTITY_ID: config[CONF_ENTITY_ID],
            state_trigger.CONF_TO: to_state,
        }
        state_config = state_trigger.TRIGGER_SCHEMA(state_config)
        return await state_trigger.async_attach_trigger(
            opp, state_config, action, automation_info, platform_type="device"
        )

    if config[CONF_TYPE] == "position":
        position = "current_position"
    if config[CONF_TYPE] == "tilt_position":
        position = "current_tilt_position"
    min_pos = config.get(CONF_ABOVE, -1)
    max_pos = config.get(CONF_BELOW, 101)
    value_template = f"{{{{ state.attributes.{position} }}}}"

    numeric_state_config = {
        CONF_PLATFORM: "numeric_state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        CONF_BELOW: max_pos,
        CONF_ABOVE: min_pos,
        CONF_VALUE_TEMPLATE: value_template,
    }
    numeric_state_config = numeric_state_trigger.TRIGGER_SCHEMA(numeric_state_config)
    return await numeric_state_trigger.async_attach_trigger(
        opp, numeric_state_config, action, automation_info, platform_type="device"
    )
