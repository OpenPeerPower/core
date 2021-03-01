"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.counter import (
    DOMAIN,
    SERVICE_DECREMENT,
    SERVICE_INCREMENT,
    SERVICE_RESET,
)
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.core import callback
from openpeerpower.loader import bind_opp


@callback
@bind_opp
def async_increment(opp, entity_id):
    """Increment a counter."""
    opp.async_add_job(
        opp.services.async_call(DOMAIN, SERVICE_INCREMENT, {ATTR_ENTITY_ID: entity_id})
    )


@callback
@bind_opp
def async_decrement(opp, entity_id):
    """Decrement a counter."""
    opp.async_add_job(
        opp.services.async_call(DOMAIN, SERVICE_DECREMENT, {ATTR_ENTITY_ID: entity_id})
    )


@callback
@bind_opp
def async_reset(opp, entity_id):
    """Reset a counter."""
    opp.async_add_job(
        opp.services.async_call(DOMAIN, SERVICE_RESET, {ATTR_ENTITY_ID: entity_id})
    )
