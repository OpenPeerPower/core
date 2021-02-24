"""Provides device actions for Number."""
from typing import Any, Dict, List, Optional

import voluptuous as vol

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from openpeerpower.core import Context, OpenPeerPower
from openpeerpower.helpers import entity_registry
import openpeerpower.helpers.config_validation as cv

from . import DOMAIN, const

ATYP_SET_VALUE = "set_value"

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): ATYP_SET_VALUE,
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(DOMAIN),
        vol.Required(const.ATTR_VALUE): vol.Coerce(float),
    }
)


async def async_get_actions(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device actions for Number."""
    registry = await entity_registry.async_get_registry(opp)
    actions: List[Dict[str, Any]] = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        actions.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: ATYP_SET_VALUE,
            }
        )

    return actions


async def async_call_action_from_config(
    opp: OpenPeerPower, config: dict, variables: dict, context: Optional[Context]
) -> None:
    """Execute a device action."""
    config = ACTION_SCHEMA(config)

    if config[CONF_TYPE] != ATYP_SET_VALUE:
        return

    await opp.services.async_call(
        DOMAIN,
        const.SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: config[CONF_ENTITY_ID],
            const.ATTR_VALUE: config[const.ATTR_VALUE],
        },
        blocking=True,
        context=context,
    )


async def async_get_action_capabilities(opp: OpenPeerPower, config: dict) -> dict:
    """List action capabilities."""
    action_type = config[CONF_TYPE]

    if action_type != ATYP_SET_VALUE:
        return {}

    fields = {vol.Required(const.ATTR_VALUE): vol.Coerce(float)}

    return {"extra_fields": vol.Schema(fields)}
