"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.image_processing import DOMAIN, SERVICE_SCAN
from openpeerpower.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL
from openpeerpower.core import callback
from openpeerpower.loader import bind.opp


@bind.opp
def scan.opp, entity_id=ENTITY_MATCH_ALL):
    """Force process of all cameras or given entity."""
   .opp.add_job(async_scan,.opp, entity_id)


@callback
@bind.opp
def async_scan.opp, entity_id=ENTITY_MATCH_ALL):
    """Force process of all cameras or given entity."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
   .opp.async_add_job.opp.services.async_call(DOMAIN, SERVICE_SCAN, data))
