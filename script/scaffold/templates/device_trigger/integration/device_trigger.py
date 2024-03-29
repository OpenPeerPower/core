"""Provides device triggers for NEW_NAME."""
from __future__ import annotations

import voluptuous as vol

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.components.openpeerpower.triggers import state
from openpeerpower.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.core import CALLBACK_TYPE, OpenPeerPower
from openpeerpower.helpers import config_validation as cv, entity_registry
from openpeerpower.helpers.typing import ConfigType

from . import DOMAIN

# TODO specify your supported trigger types.
TRIGGER_TYPES = {"turned_on", "turned_off"}

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> list[dict]:
    """List device triggers for NEW_NAME devices."""
    registry = await entity_registry.async_get_registry(opp)
    triggers = []

    # TODO Read this comment and remove it.
    # This example shows how to iterate over the entities of this device
    # that match this integration. If your triggers instead rely on
    # events fired by devices without entities, do something like:
    # zha_device = await _async_get_zha_device(opp, device_id)
    # return zha_device.device_triggers

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        # Add triggers for each entity that belongs to this integration
        # TODO add your own triggers.
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "turned_on",
            }
        )
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "turned_off",
            }
        )

    return triggers


async def async_attach_trigger(
    opp: OpenPeerPower,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    # TODO Implement your own logic to attach triggers.
    # Use the existing state or event triggers from the automation integration.

    if config[CONF_TYPE] == "turned_on":
        to_state = STATE_ON
    else:
        to_state = STATE_OFF

    state_config = {
        state.CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state.CONF_TO: to_state,
    }
    state_config = state.TRIGGER_SCHEMA(state_config)
    return await state.async_attach_trigger(
        opp, state_config, action, automation_info, platform_type="device"
    )
