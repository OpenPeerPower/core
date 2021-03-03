"""Support for LCN covers."""
import pypck

from openpeerpower.components.cover import CoverEntity
from openpeerpower.const import CONF_ADDRESS

from . import LcnEntity
from .const import CONF_CONNECTIONS, CONF_MOTOR, CONF_REVERSE_TIME, DATA_LCN
from .helpers import get_connection

PARALLEL_UPDATES = 0


async def async_setup_platform(
    opp, opp_config, async_add_entities, discovery_info=None
):
    """Setups the LCN cover platform."""
    if discovery_info is None:
        return

    devices = []
    for config in discovery_info:
        address, connection_id = config[CONF_ADDRESS]
        addr = pypck.lcn_addr.LcnAddr(*address)
        connections = opp.data[DATA_LCN][CONF_CONNECTIONS]
        connection = get_connection(connections, connection_id)
        address_connection = connection.get_address_conn(addr)

        if config[CONF_MOTOR] == "OUTPUTS":
            devices.append(LcnOutputsCover(config, address_connection))
        else:  # RELAYS
            devices.append(LcnRelayCover(config, address_connection))

    async_add_entities(devices)


class LcnOutputsCover(LcnEntity, CoverEntity):
    """Representation of a LCN cover connected to output ports."""

    def __init__(self, config, device_connection):
        """Initialize the LCN cover."""
        super().__init__(config, device_connection)

        self.output_ids = [
            pypck.lcn_defs.OutputPort["OUTPUTUP"].value,
            pypck.lcn_defs.OutputPort["OUTPUTDOWN"].value,
        ]
        if CONF_REVERSE_TIME in config:
            self.reverse_time = pypck.lcn_defs.MotorReverseTime[
                config[CONF_REVERSE_TIME]
            ]
        else:
            self.reverse_time = None

        self._is_closed = False
        self._is_closing = False
        self._is_opening = False

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        await self.device_connection.activate_status_request_handler(
            pypck.lcn_defs.OutputPort["OUTPUTUP"]
        )
        await self.device_connection.activate_status_request_handler(
            pypck.lcn_defs.OutputPort["OUTPUTDOWN"]
        )

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self._is_closed

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self._is_opening

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self._is_closing

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the entity."""
        return True

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        state = pypck.lcn_defs.MotorStateModifier.DOWN
        if not await self.device_connection.control_motors_outputs(
            state, self.reverse_time
        ):
            return
        self._is_opening = False
        self._is_closing = True
        self.async_write_op_state()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        state = pypck.lcn_defs.MotorStateModifier.UP
        if not await self.device_connection.control_motors_outputs(
            state, self.reverse_time
        ):
            return
        self._is_closed = False
        self._is_opening = True
        self._is_closing = False
        self.async_write_op_state()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        state = pypck.lcn_defs.MotorStateModifier.STOP
        if not await self.device_connection.control_motors_outputs(state):
            return
        self._is_closing = False
        self._is_opening = False
        self.async_write_op_state()

    def input_received(self, input_obj):
        """Set cover states when LCN input object (command) is received."""
        if (
            not isinstance(input_obj, pypck.inputs.ModStatusOutput)
            or input_obj.get_output_id() not in self.output_ids
        ):
            return

        if input_obj.get_percent() > 0:  # motor is on
            if input_obj.get_output_id() == self.output_ids[0]:
                self._is_opening = True
                self._is_closing = False
            else:  # self.output_ids[1]
                self._is_opening = False
                self._is_closing = True
            self._is_closed = self._is_closing
        else:  # motor is off
            # cover is assumed to be closed if we were in closing state before
            self._is_closed = self._is_closing
            self._is_closing = False
            self._is_opening = False

        self.async_write_op_state()


class LcnRelayCover(LcnEntity, CoverEntity):
    """Representation of a LCN cover connected to relays."""

    def __init__(self, config, device_connection):
        """Initialize the LCN cover."""
        super().__init__(config, device_connection)

        self.motor = pypck.lcn_defs.MotorPort[config[CONF_MOTOR]]
        self.motor_port_onoff = self.motor.value * 2
        self.motor_port_updown = self.motor_port_onoff + 1

        self._is_closed = False
        self._is_closing = False
        self._is_opening = False

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        if not self.device_connection.is_group:
            await self.device_connection.activate_status_request_handler(self.motor)

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self._is_closed

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self._is_opening

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self._is_closing

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the entity."""
        return True

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        states = [pypck.lcn_defs.MotorStateModifier.NOCHANGE] * 4
        states[self.motor.value] = pypck.lcn_defs.MotorStateModifier.DOWN
        if not await self.device_connection.control_motors_relays(states):
            return
        self._is_opening = False
        self._is_closing = True
        self.async_write_op_state()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        states = [pypck.lcn_defs.MotorStateModifier.NOCHANGE] * 4
        states[self.motor.value] = pypck.lcn_defs.MotorStateModifier.UP
        if not await self.device_connection.control_motors_relays(states):
            return
        self._is_closed = False
        self._is_opening = True
        self._is_closing = False
        self.async_write_op_state()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        states = [pypck.lcn_defs.MotorStateModifier.NOCHANGE] * 4
        states[self.motor.value] = pypck.lcn_defs.MotorStateModifier.STOP
        if not await self.device_connection.control_motors_relays(states):
            return
        self._is_closing = False
        self._is_opening = False
        self.async_write_op_state()

    def input_received(self, input_obj):
        """Set cover states when LCN input object (command) is received."""
        if not isinstance(input_obj, pypck.inputs.ModStatusRelays):
            return

        states = input_obj.states  # list of boolean values (relay on/off)
        if states[self.motor_port_onoff]:  # motor is on
            self._is_opening = not states[self.motor_port_updown]  # set direction
            self._is_closing = states[self.motor_port_updown]  # set direction
        else:  # motor is off
            self._is_opening = False
            self._is_closing = False
            self._is_closed = states[self.motor_port_updown]

        self.async_write_op_state()
