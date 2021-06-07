"""Support for LCN covers."""

import pypck

from openpeerpower.components.cover import DOMAIN as DOMAIN_COVER, CoverEntity
from openpeerpower.const import CONF_ADDRESS, CONF_DOMAIN, CONF_ENTITIES

from . import LcnEntity
from .const import CONF_DOMAIN_DATA, CONF_MOTOR, CONF_REVERSE_TIME
from .helpers import get_device_connection

PARALLEL_UPDATES = 0


def create_lcn_cover_entity(opp, entity_config, config_entry):
    """Set up an entity for this domain."""
    device_connection = get_device_connection(
        opp, tuple(entity_config[CONF_ADDRESS]), config_entry
    )

    if entity_config[CONF_DOMAIN_DATA][CONF_MOTOR] in "OUTPUTS":
        return LcnOutputsCover(entity_config, config_entry.entry_id, device_connection)
    # in RELAYS
    return LcnRelayCover(entity_config, config_entry.entry_id, device_connection)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up LCN cover entities from a config entry."""
    entities = []

    for entity_config in config_entry.data[CONF_ENTITIES]:
        if entity_config[CONF_DOMAIN] == DOMAIN_COVER:
            entities.append(create_lcn_cover_entity(opp, entity_config, config_entry))

    async_add_entities(entities)


class LcnOutputsCover(LcnEntity, CoverEntity):
    """Representation of a LCN cover connected to output ports."""

    def __init__(self, config, entry_id, device_connection):
        """Initialize the LCN cover."""
        super().__init__(config, entry_id, device_connection)

        self.output_ids = [
            pypck.lcn_defs.OutputPort["OUTPUTUP"].value,
            pypck.lcn_defs.OutputPort["OUTPUTDOWN"].value,
        ]
        if CONF_REVERSE_TIME in config[CONF_DOMAIN_DATA]:
            self.reverse_time = pypck.lcn_defs.MotorReverseTime[
                config[CONF_DOMAIN_DATA][CONF_REVERSE_TIME]
            ]
        else:
            self.reverse_time = None

        self._is_closed = False
        self._is_closing = False
        self._is_opening = False

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        if not self.device_connection.is_group:
            await self.device_connection.activate_status_request_handler(
                pypck.lcn_defs.OutputPort["OUTPUTUP"]
            )
            await self.device_connection.activate_status_request_handler(
                pypck.lcn_defs.OutputPort["OUTPUTDOWN"]
            )

    async def async_will_remove_from_opp(self):
        """Run when entity will be removed from opp."""
        await super().async_will_remove_from_opp()
        if not self.device_connection.is_group:
            await self.device_connection.cancel_status_request_handler(
                pypck.lcn_defs.OutputPort["OUTPUTUP"]
            )
            await self.device_connection.cancel_status_request_handler(
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

    def __init__(self, config, entry_id, device_connection):
        """Initialize the LCN cover."""
        super().__init__(config, entry_id, device_connection)

        self.motor = pypck.lcn_defs.MotorPort[config[CONF_DOMAIN_DATA][CONF_MOTOR]]
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

    async def async_will_remove_from_opp(self):
        """Run when entity will be removed from opp."""
        await super().async_will_remove_from_opp()
        if not self.device_connection.is_group:
            await self.device_connection.cancel_status_request_handler(self.motor)

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
