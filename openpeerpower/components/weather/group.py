"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.core import OpenPeerPower, callback


@callback
def async_describe_on_off_states(
    opp: OpenPeerPower, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.exclude_domain()
