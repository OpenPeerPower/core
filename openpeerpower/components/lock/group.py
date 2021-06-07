"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.const import STATE_LOCKED, STATE_UNLOCKED
from openpeerpower.core import OpenPeerPower, callback


@callback
def async_describe_on_off_states(
    opp: OpenPeerPower, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states({STATE_LOCKED}, STATE_UNLOCKED)
