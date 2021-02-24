"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.group import (
    ATTR_ADD_ENTITIES,
    ATTR_ENTITIES,
    ATTR_OBJECT_ID,
    DOMAIN,
    SERVICE_REMOVE,
    SERVICE_SET,
)
from openpeerpower.const import ATTR_ICON, ATTR_NAME, SERVICE_RELOAD
from openpeerpower.core import callback
from openpeerpower.loader import bind.opp


@bind.opp
def reload.opp):
    """Reload the automation from config."""
    opp.add_job(async_reload, opp)


@callback
@bind.opp
def async_reload(opp):
    """Reload the automation from config."""
    opp.async_add_job(opp.services.async_call(DOMAIN, SERVICE_RELOAD))


@bind.opp
def set_group(
    opp,
    object_id,
    name=None,
    entity_ids=None,
    icon=None,
    add=None,
):
    """Create/Update a group."""
    opp.add_job(
        async_set_group,
        opp,
        object_id,
        name,
        entity_ids,
        icon,
        add,
    )


@callback
@bind.opp
def async_set_group(
    opp,
    object_id,
    name=None,
    entity_ids=None,
    icon=None,
    add=None,
):
    """Create/Update a group."""
    data = {
        key: value
        for key, value in [
            (ATTR_OBJECT_ID, object_id),
            (ATTR_NAME, name),
            (ATTR_ENTITIES, entity_ids),
            (ATTR_ICON, icon),
            (ATTR_ADD_ENTITIES, add),
        ]
        if value is not None
    }

    opp.async_add_job(opp.services.async_call(DOMAIN, SERVICE_SET, data))


@callback
@bind.opp
def async_remove(opp, object_id):
    """Remove a user group."""
    data = {ATTR_OBJECT_ID: object_id}
    opp.async_add_job(opp.services.async_call(DOMAIN, SERVICE_REMOVE, data))
