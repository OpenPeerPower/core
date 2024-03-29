"""Support for LCN switches."""

import pypck

from openpeerpower.components.switch import DOMAIN as DOMAIN_SWITCH, SwitchEntity
from openpeerpower.const import CONF_ADDRESS, CONF_DOMAIN, CONF_ENTITIES

from . import LcnEntity
from .const import CONF_DOMAIN_DATA, CONF_OUTPUT, OUTPUT_PORTS
from .helpers import get_device_connection

PARALLEL_UPDATES = 0


def create_lcn_switch_entity(opp, entity_config, config_entry):
    """Set up an entity for this domain."""
    device_connection = get_device_connection(
        opp, tuple(entity_config[CONF_ADDRESS]), config_entry
    )

    if entity_config[CONF_DOMAIN_DATA][CONF_OUTPUT] in OUTPUT_PORTS:
        return LcnOutputSwitch(entity_config, config_entry.entry_id, device_connection)
    # in RELAY_PORTS
    return LcnRelaySwitch(entity_config, config_entry.entry_id, device_connection)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up LCN switch entities from a config entry."""

    entities = []

    for entity_config in config_entry.data[CONF_ENTITIES]:
        if entity_config[CONF_DOMAIN] == DOMAIN_SWITCH:
            entities.append(create_lcn_switch_entity(opp, entity_config, config_entry))

    async_add_entities(entities)


class LcnOutputSwitch(LcnEntity, SwitchEntity):
    """Representation of a LCN switch for output ports."""

    def __init__(self, config, entry_id, device_connection):
        """Initialize the LCN switch."""
        super().__init__(config, entry_id, device_connection)

        self.output = pypck.lcn_defs.OutputPort[config[CONF_DOMAIN_DATA][CONF_OUTPUT]]

        self._is_on = None

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        if not self.device_connection.is_group:
            await self.device_connection.activate_status_request_handler(self.output)

    async def async_will_remove_from_opp(self):
        """Run when entity will be removed from opp."""
        await super().async_will_remove_from_opp()
        if not self.device_connection.is_group:
            await self.device_connection.cancel_status_request_handler(self.output)

    @property
    def is_on(self):
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        if not await self.device_connection.dim_output(self.output.value, 100, 0):
            return
        self._is_on = True
        self.async_write_op_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        if not await self.device_connection.dim_output(self.output.value, 0, 0):
            return
        self._is_on = False
        self.async_write_op_state()

    def input_received(self, input_obj):
        """Set switch state when LCN input object (command) is received."""
        if (
            not isinstance(input_obj, pypck.inputs.ModStatusOutput)
            or input_obj.get_output_id() != self.output.value
        ):
            return

        self._is_on = input_obj.get_percent() > 0
        self.async_write_op_state()


class LcnRelaySwitch(LcnEntity, SwitchEntity):
    """Representation of a LCN switch for relay ports."""

    def __init__(self, config, entry_id, device_connection):
        """Initialize the LCN switch."""
        super().__init__(config, entry_id, device_connection)

        self.output = pypck.lcn_defs.RelayPort[config[CONF_DOMAIN_DATA][CONF_OUTPUT]]

        self._is_on = None

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        if not self.device_connection.is_group:
            await self.device_connection.activate_status_request_handler(self.output)

    async def async_will_remove_from_opp(self):
        """Run when entity will be removed from opp."""
        await super().async_will_remove_from_opp()
        if not self.device_connection.is_group:
            await self.device_connection.cancel_status_request_handler(self.output)

    @property
    def is_on(self):
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        states = [pypck.lcn_defs.RelayStateModifier.NOCHANGE] * 8
        states[self.output.value] = pypck.lcn_defs.RelayStateModifier.ON
        if not await self.device_connection.control_relays(states):
            return
        self._is_on = True
        self.async_write_op_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        states = [pypck.lcn_defs.RelayStateModifier.NOCHANGE] * 8
        states[self.output.value] = pypck.lcn_defs.RelayStateModifier.OFF
        if not await self.device_connection.control_relays(states):
            return
        self._is_on = False
        self.async_write_op_state()

    def input_received(self, input_obj):
        """Set switch state when LCN input object (command) is received."""
        if not isinstance(input_obj, pypck.inputs.ModStatusRelays):
            return

        self._is_on = input_obj.get_state(self.output.value)
        self.async_write_op_state()
