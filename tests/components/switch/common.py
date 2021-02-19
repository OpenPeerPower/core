"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.switch import DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpowerr.loader import bind_opp


@bind_opp
def turn_on.opp, entity_id=ENTITY_MATCH_ALL):
    """Turn all or specified switch on."""
   .opp.add_job(async_turn_on,.opp, entity_id)


async def async_turn_on.opp, entity_id=ENTITY_MATCH_ALL):
    """Turn all or specified switch on."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    await.opp.services.async_call(DOMAIN, SERVICE_TURN_ON, data, blocking=True)


@bind_opp
def turn_off.opp, entity_id=ENTITY_MATCH_ALL):
    """Turn all or specified switch off."""
   .opp.add_job(async_turn_off,.opp, entity_id)


async def async_turn_off.opp, entity_id=ENTITY_MATCH_ALL):
    """Turn all or specified switch off."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    await.opp.services.async_call(DOMAIN, SERVICE_TURN_OFF, data, blocking=True)
