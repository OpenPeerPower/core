"""Describe group states."""


from openpeerpower.components.group import GroupIntegrationRegistry
from openpeerpower.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_TRIGGERED,
    STATE_OFF,
)
from openpeerpower.core import callback
from openpeerpower.helpers.typing import OpenPeerPowerType


@callback
def async_describe_on_off_states(
    opp: OpenPeerPowerType, registry: GroupIntegrationRegistry
) -> None:
    """Describe group on off states."""
    registry.on_off_states(
        {
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_CUSTOM_BYPASS,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_TRIGGERED,
        },
        STATE_OFF,
    )
