"""Provides device actions for NEW_NAME."""
from __future__ import annotations

import voluptuous as vol

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.core import Context, OpenPeerPower
from openpeerpower.helpers import entity_registry
import openpeerpower.helpers.config_validation as cv

from . import DOMAIN

# TODO specify your supported action types.
ACTION_TYPES = {"turn_on", "turn_off"}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(DOMAIN),
    }
)


async def async_get_actions(opp: OpenPeerPower, device_id: str) -> list[dict]:
    """List device actions for NEW_NAME devices."""
    registry = await entity_registry.async_get_registry(opp)
    actions = []

    # TODO Read this comment and remove it.
    # This example shows how to iterate over the entities of this device
    # that match this integration. If your actions instead rely on
    # calling services, do something like:
    # zha_device = await _async_get_zha_device(opp, device_id)
    # return zha_device.device_actions

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        # Add actions for each entity that belongs to this integration
        # TODO add your own actions.
        actions.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "turn_on",
            }
        )
        actions.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "turn_off",
            }
        )

    return actions


async def async_call_action_from_config(
    opp: OpenPeerPower, config: dict, variables: dict, context: Context | None
) -> None:
    """Execute a device action."""
    service_data = {ATTR_ENTITY_ID: config[CONF_ENTITY_ID]}

    if config[CONF_TYPE] == "turn_on":
        service = SERVICE_TURN_ON
    elif config[CONF_TYPE] == "turn_off":
        service = SERVICE_TURN_OFF

    await opp.services.async_call(
        DOMAIN, service, service_data, blocking=True, context=context
    )
