"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.const import STATE_OFF
from openpeerpower.core import OpenPeerPower, callback

from .const import HVAC_MODE_OFF, HVAC_MODES


@callback
def async_describe_on_off_states(
    opp: OpenPeerPower, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states(
        set(HVAC_MODES) - {HVAC_MODE_OFF},
        STATE_OFF,
    )
