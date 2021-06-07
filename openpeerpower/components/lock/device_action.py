"""Provides device automations for Lock."""
from __future__ import annotations

import voluptuous as vol

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    SERVICE_LOCK,
    SERVICE_OPEN,
    SERVICE_UNLOCK,
)
from openpeerpower.core import Context, OpenPeerPower
from openpeerpower.helpers import entity_registry
import openpeerpower.helpers.config_validation as cv

from . import DOMAIN, SUPPORT_OPEN

ACTION_TYPES = {"lock", "unlock", "open"}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(DOMAIN),
    }
)


async def async_get_actions(opp: OpenPeerPower, device_id: str) -> list[dict]:
    """List device actions for Lock devices."""
    registry = await entity_registry.async_get_registry(opp)
    actions = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        # Add actions for each entity that belongs to this integration
        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.entity_id,
        }

        actions.append({**base_action, CONF_TYPE: "lock"})
        actions.append({**base_action, CONF_TYPE: "unlock"})

        state = opp.states.get(entry.entity_id)
        if state:
            features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
            if features & (SUPPORT_OPEN):
                actions.append({**base_action, CONF_TYPE: "open"})

    return actions


async def async_call_action_from_config(
    opp: OpenPeerPower, config: dict, variables: dict, context: Context | None
) -> None:
    """Execute a device action."""
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if config[CONF_TYPE] == "lock":
        service = SERVICE_LOCK
    elif config[CONF_TYPE] == "unlock":
        service = SERVICE_UNLOCK
    elif config[CONF_TYPE] == "open":
        service = SERVICE_OPEN

    await opp.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )
