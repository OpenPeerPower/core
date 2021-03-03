"""Support for LCN lights."""
import pypck

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_TRANSITION,
    LightEntity,
)
from openpeerpower.const import CONF_ADDRESS

from . import LcnEntity
from .const import (
    CONF_CONNECTIONS,
    CONF_DIMMABLE,
    CONF_OUTPUT,
    CONF_TRANSITION,
    DATA_LCN,
    OUTPUT_PORTS,
)
from .helpers import get_connection

PARALLEL_UPDATES = 0


async def async_setup_platform(
    opp, opp_config, async_add_entities, discovery_info=None
):
    """Set up the LCN light platform."""
    if discovery_info is None:
        return

    devices = []
    for config in discovery_info:
        address, connection_id = config[CONF_ADDRESS]
        addr = pypck.lcn_addr.LcnAddr(*address)
        connections = opp.data[DATA_LCN][CONF_CONNECTIONS]
        connection = get_connection(connections, connection_id)
        address_connection = connection.get_address_conn(addr)

        if config[CONF_OUTPUT] in OUTPUT_PORTS:
            device = LcnOutputLight(config, address_connection)
        else:  # in RELAY_PORTS
            device = LcnRelayLight(config, address_connection)

        devices.append(device)

    async_add_entities(devices)


class LcnOutputLight(LcnEntity, LightEntity):
    """Representation of a LCN light for output ports."""

    def __init__(self, config, device_connection):
        """Initialize the LCN light."""
        super().__init__(config, device_connection)

        self.output = pypck.lcn_defs.OutputPort[config[CONF_OUTPUT]]

        self._transition = pypck.lcn_defs.time_to_ramp_value(config[CONF_TRANSITION])
        self.dimmable = config[CONF_DIMMABLE]

        self._brightness = 255
        self._is_on = None
        self._is_dimming_to_zero = False

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        if not self.device_connection.is_group:
            await self.device_connection.activate_status_request_handler(self.output)

    @property
    def supported_features(self):
        """Flag supported features."""
        if self.dimmable:
            return SUPPORT_TRANSITION | SUPPORT_BRIGHTNESS
        return SUPPORT_TRANSITION

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def is_on(self):
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        if ATTR_BRIGHTNESS in kwargs:
            percent = int(kwargs[ATTR_BRIGHTNESS] / 255.0 * 100)
        else:
            percent = 100
        if ATTR_TRANSITION in kwargs:
            transition = pypck.lcn_defs.time_to_ramp_value(
                kwargs[ATTR_TRANSITION] * 1000
            )
        else:
            transition = self._transition

        if not await self.device_connection.dim_output(
            self.output.value, percent, transition
        ):
            return
        self._is_on = True
        self._is_dimming_to_zero = False
        self.async_write_op_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        if ATTR_TRANSITION in kwargs:
            transition = pypck.lcn_defs.time_to_ramp_value(
                kwargs[ATTR_TRANSITION] * 1000
            )
        else:
            transition = self._transition

        if not await self.device_connection.dim_output(
            self.output.value, 0, transition
        ):
            return
        self._is_dimming_to_zero = bool(transition)
        self._is_on = False
        self.async_write_op_state()

    def input_received(self, input_obj):
        """Set light state when LCN input object (command) is received."""
        if (
            not isinstance(input_obj, pypck.inputs.ModStatusOutput)
            or input_obj.get_output_id() != self.output.value
        ):
            return

        self._brightness = int(input_obj.get_percent() / 100.0 * 255)
        if self.brightness == 0:
            self._is_dimming_to_zero = False
        if not self._is_dimming_to_zero:
            self._is_on = self.brightness > 0
        self.async_write_op_state()


class LcnRelayLight(LcnEntity, LightEntity):
    """Representation of a LCN light for relay ports."""

    def __init__(self, config, device_connection):
        """Initialize the LCN light."""
        super().__init__(config, device_connection)

        self.output = pypck.lcn_defs.RelayPort[config[CONF_OUTPUT]]

        self._is_on = None

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""
        await super().async_added_to_opp()
        if not self.device_connection.is_group:
            await self.device_connection.activate_status_request_handler(self.output)

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
        """Set light state when LCN input object (command) is received."""
        if not isinstance(input_obj, pypck.inputs.ModStatusRelays):
            return

        self._is_on = input_obj.get_state(self.output.value)
        self.async_write_op_state()
