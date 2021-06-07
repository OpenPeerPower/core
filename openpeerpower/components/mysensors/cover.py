"""Support for MySensors covers."""
from enum import Enum, unique
import logging

from openpeerpower.components import mysensors
from openpeerpower.components.cover import ATTR_POSITION, DOMAIN, CoverEntity
from openpeerpower.components.mysensors import on_unload
from openpeerpower.components.mysensors.const import MYSENSORS_DISCOVERY
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


@unique
class CoverState(Enum):
    """An enumeration of the standard cover states."""

    OPEN = 0
    OPENING = 1
    CLOSING = 2
    CLOSED = 3


async def async_setup_entry(
    opp: OpenPeerPower,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up this platform for a specific ConfigEntry(==Gateway)."""

    async def async_discover(discovery_info):
        """Discover and add a MySensors cover."""
        mysensors.setup_mysensors_platform(
            opp,
            DOMAIN,
            discovery_info,
            MySensorsCover,
            async_add_entities=async_add_entities,
        )

    await on_unload(
        opp,
        config_entry.entry_id,
        async_dispatcher_connect(
            opp,
            MYSENSORS_DISCOVERY.format(config_entry.entry_id, DOMAIN),
            async_discover,
        ),
    )


class MySensorsCover(mysensors.device.MySensorsEntity, CoverEntity):
    """Representation of the value of a MySensors Cover child node."""

    def get_cover_state(self):
        """Return a CoverState enum representing the state of the cover."""
        set_req = self.gateway.const.SetReq
        v_up = self._values.get(set_req.V_UP) == STATE_ON
        v_down = self._values.get(set_req.V_DOWN) == STATE_ON
        v_stop = self._values.get(set_req.V_STOP) == STATE_ON

        # If a V_DIMMER or V_PERCENTAGE is available, that is the amount
        # the cover is open. Otherwise, use 0 or 100 based on the V_LIGHT
        # or V_STATUS.
        amount = 100
        if set_req.V_DIMMER in self._values:
            amount = self._values.get(set_req.V_DIMMER)
        else:
            amount = 100 if self._values.get(set_req.V_LIGHT) == STATE_ON else 0

        if amount == 0:
            return CoverState.CLOSED
        if v_up and not v_down and not v_stop:
            return CoverState.OPENING
        if not v_up and v_down and not v_stop:
            return CoverState.CLOSING
        return CoverState.OPEN

    @property
    def is_closed(self):
        """Return True if the cover is closed."""
        return self.get_cover_state() == CoverState.CLOSED

    @property
    def is_closing(self):
        """Return True if the cover is closing."""
        return self.get_cover_state() == CoverState.CLOSING

    @property
    def is_opening(self):
        """Return True if the cover is opening."""
        return self.get_cover_state() == CoverState.OPENING

    @property
    def current_cover_position(self):
        """Return current position of cover.

        None is unknown, 0 is closed, 100 is fully open.
        """
        set_req = self.gateway.const.SetReq
        return self._values.get(set_req.V_DIMMER)

    async def async_open_cover(self, **kwargs):
        """Move the cover up."""
        set_req = self.gateway.const.SetReq
        self.gateway.set_child_value(
            self.node_id, self.child_id, set_req.V_UP, 1, ack=1
        )
        if self.assumed_state:
            # Optimistically assume that cover has changed state.
            if set_req.V_DIMMER in self._values:
                self._values[set_req.V_DIMMER] = 100
            else:
                self._values[set_req.V_LIGHT] = STATE_ON
            self.async_write_op_state()

    async def async_close_cover(self, **kwargs):
        """Move the cover down."""
        set_req = self.gateway.const.SetReq
        self.gateway.set_child_value(
            self.node_id, self.child_id, set_req.V_DOWN, 1, ack=1
        )
        if self.assumed_state:
            # Optimistically assume that cover has changed state.
            if set_req.V_DIMMER in self._values:
                self._values[set_req.V_DIMMER] = 0
            else:
                self._values[set_req.V_LIGHT] = STATE_OFF
            self.async_write_op_state()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        set_req = self.gateway.const.SetReq
        self.gateway.set_child_value(
            self.node_id, self.child_id, set_req.V_DIMMER, position, ack=1
        )
        if self.assumed_state:
            # Optimistically assume that cover has changed state.
            self._values[set_req.V_DIMMER] = position
            self.async_write_op_state()

    async def async_stop_cover(self, **kwargs):
        """Stop the device."""
        set_req = self.gateway.const.SetReq
        self.gateway.set_child_value(
            self.node_id, self.child_id, set_req.V_STOP, 1, ack=1
        )
