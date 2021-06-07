"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.const import STATE_OFF
from openpeerpower.core import OpenPeerPower, callback

from . import (
    STATE_ECO,
    STATE_ELECTRIC,
    STATE_GAS,
    STATE_HEAT_PUMP,
    STATE_HIGH_DEMAND,
    STATE_PERFORMANCE,
)


@callback
def async_describe_on_off_states(
    opp: OpenPeerPower, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states(
        {
            STATE_ECO,
            STATE_ELECTRIC,
            STATE_PERFORMANCE,
            STATE_HIGH_DEMAND,
            STATE_HEAT_PUMP,
            STATE_GAS,
        },
        STATE_OFF,
    )
