"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.core import callback
from openpeerpower.helpers.typing import OpenPeerPowerType


@callback
def async_describe_on_off_states(
    opp: OpenPeerPowerType, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.exclude_domain()
