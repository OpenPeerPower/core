"""Provides device automations for Arcam FMJ Receiver control."""
from __future__ import annotations

import voluptuous as vol

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
)
from openpeerpower.core import CALLBACK_TYPE, Event, OpenPeerPower, OppJob, callback
from openpeerpower.helpers import config_validation as cv, entity_registry
from openpeerpower.helpers.typing import ConfigType

from .const import DOMAIN, EVENT_TURN_ON

TRIGGER_TYPES = {"turn_on"}
TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> list[dict]:
    """List device triggers for Arcam FMJ Receiver control devices."""
    registry = await entity_registry.async_get_registry(opp)
    triggers = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain == "media_player":
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "turn_on",
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
    trigger_id = automation_info.get("trigger_id") if automation_info else None
    job = OppJob(action)

    if config[CONF_TYPE] == "turn_on":
        entity_id = config[CONF_ENTITY_ID]

        @callback
        def _handle_event(event: Event):
            if event.data[ATTR_ENTITY_ID] == entity_id:
                opp.async_run_opp_job(
                    job,
                    {
                        "trigger": {
                            **config,
                            "description": f"{DOMAIN} - {entity_id}",
                            "id": trigger_id,
                        }
                    },
                    event.context,
                )

        return opp.bus.async_listen(EVENT_TURN_ON, _handle_event)

    return lambda: None
