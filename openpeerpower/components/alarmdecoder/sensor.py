"""Support for AlarmDecoder sensors (Shows Panel Display)."""
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import SIGNAL_PANEL_MESSAGE


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
):
    """Set up for AlarmDecoder sensor."""

    entity = AlarmDecoderSensor()
    async_add_entities([entity])
    return True


class AlarmDecoderSensor(Entity):
    """Representation of an AlarmDecoder keypad."""

    def __init__(self):
        """Initialize the alarm panel."""
        self._display = ""
        self._state = None
        self._icon = "mdi:alarm-check"
        self._name = "Alarm Panel Display"

    async def async_added_to_opp(self):
        """Register callbacks."""
        self.async_on_remove(
            self.opp.helpers.dispatcher.async_dispatcher_connect(
                SIGNAL_PANEL_MESSAGE, self._message_callback
            )
        )

    def _message_callback(self, message):
        if self._display != message.text:
            self._display = message.text
            self.schedule_update_op_state()

    @property
    def icon(self):
        """Return the icon if any."""
        return self._icon

    @property
    def state(self):
        """Return the overall state."""
        return self._display

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False
