"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.core import OpenPeerPower, callback

from . import STATE_CLEANING, STATE_ERROR, STATE_RETURNING


@callback
def async_describe_on_off_states(
    opp: OpenPeerPower, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states(
        {STATE_CLEANING, STATE_ON, STATE_RETURNING, STATE_ERROR}, STATE_OFF
    )
