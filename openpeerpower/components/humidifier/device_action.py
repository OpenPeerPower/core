"""Provides device actions for Humidifier."""
from typing import List, Optional

import voluptuous as vol

from openpeerpower.components.device_automation import toggle_entity
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    ATTR_SUPPORTED_FEATURES,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from openpeerpower.core import Context, OpenPeerPower
from openpeerpower.helpers import entity_registry
import openpeerpower.helpers.config_validation as cv

from . import DOMAIN, const

SET_HUMIDITY_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): "set_humidity",
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(DOMAIN),
        vol.Required(const.ATTR_HUMIDITY): vol.Coerce(int),
    }
)

SET_MODE_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): "set_mode",
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(DOMAIN),
        vol.Required(ATTR_MODE): cv.string,
    }
)

ONOFF_SCHEMA = toggle_entity.ACTION_SCHEMA.extend({vol.Required(CONF_DOMAIN): DOMAIN})

ACTION_SCHEMA = vol.Any(SET_HUMIDITY_SCHEMA, SET_MODE_SCHEMA, ONOFF_SCHEMA)


async def async_get_actions(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device actions for Humidifier devices."""
    registry = await entity_registry.async_get_registry(opp)
    actions = await toggle_entity.async_get_actions(opp, device_id, DOMAIN)

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = opp.states.get(entry.entity_id)

        actions.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "set_humidity",
            }
        )

        # We need a state or else we can't populate the available modes.
        if state is None:
            continue

        if state.attributes[ATTR_SUPPORTED_FEATURES] & const.SUPPORT_MODES:
            actions.append(
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "set_mode",
                }
            )

    return actions


async def async_call_action_from_config(
    opp: OpenPeerPower, config: dict, variables: dict, context: Optional[Context]
) -> None:
    """Execute a device action."""
    config = ACTION_SCHEMA(config)

    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if config[CONF_TYPE] == "set_humidity":
        service = const.SERVICE_SET_HUMIDITY
        service_data[const.ATTR_HUMIDITY] = config[const.ATTR_HUMIDITY]
    elif config[CONF_TYPE] == "set_mode":
        service = const.SERVICE_SET_MODE
        service_data[ATTR_MODE] = config[ATTR_MODE]
    else:
        return await toggle_entity.async_call_action_from_config(
            opp, config, variables, context, DOMAIN
        )

    await opp.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )


async def async_get_action_capabilities(opp, config):
    """List action capabilities."""
    state = opp.states.get(config[CONF_ENTITY_ID])
    action_type = config[CONF_TYPE]

    fields = {}

    if action_type == "set_humidity":
        fields[vol.Required(const.ATTR_HUMIDITY)] = vol.Coerce(int)
    elif action_type == "set_mode":
        if state:
            available_modes = state.attributes.get(const.ATTR_AVAILABLE_MODES, [])
        else:
            available_modes = []
        fields[vol.Required(ATTR_MODE)] = vol.In(available_modes)
    else:
        return {}

    return {"extra_fields": vol.Schema(fields)}
