"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpowerr.core import callback
from openpeerpowerr.helpers.typing import OpenPeerPowerType


@callback
def async_describe_on_off_states(
   .opp: OpenPeerPowerType, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states({STATE_ON}, STATE_OFF)
