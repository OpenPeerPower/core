"""Support for Tellstick switches."""
from openpeerpower.helpers.entity import ToggleEntity

from . import (
    ATTR_DISCOVER_CONFIG,
    ATTR_DISCOVER_DEVICES,
    DATA_TELLSTICK,
    DEFAULT_SIGNAL_REPETITIONS,
    TellstickDevice,
)


def setup_platform(opp, config, add_entities, discovery_info=None):
    """Set up Tellstick switches."""
    if discovery_info is None or discovery_info[ATTR_DISCOVER_DEVICES] is None:
        return

    # Allow platform level override, fallback to module config
    signal_repetitions = discovery_info.get(
        ATTR_DISCOVER_CONFIG, DEFAULT_SIGNAL_REPETITIONS
    )

    add_entities(
        [
            TellstickSwitch(opp.data[DATA_TELLSTICK][tellcore_id], signal_repetitions)
            for tellcore_id in discovery_info[ATTR_DISCOVER_DEVICES]
        ],
        True,
    )


class TellstickSwitch(TellstickDevice, ToggleEntity):
    """Representation of a Tellstick switch."""

    def _parse_op_data(self, kwargs):
        """Turn the value from OP into something useful."""

    def _parse_tellcore_data(self, tellcore_data):
        """Turn the value received from tellcore into something useful."""

    def _update_model(self, new_state, data):
        """Update the device entity state to match the arguments."""
        self._state = new_state

    def _send_device_command(self, requested_state, requested_data):
        """Let tellcore update the actual device to the requested state."""
        if requested_state:
            self._tellcore_device.turn_on()
        else:
            self._tellcore_device.turn_off()

    @property
    def force_update(self) -> bool:
        """Will trigger anytime the state property is updated."""
        return True
