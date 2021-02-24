"""Support for Tasmota binary sensors."""

from openpeerpower.components import binary_sensor
from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
import openpeerpower.helpers.event as evt

from .const import DATA_REMOVE_DISCOVER_COMPONENT
from .discovery import TASMOTA_DISCOVERY_ENTITY_NEW
from .mixins import TasmotaAvailability, TasmotaDiscoveryUpdate


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up Tasmota binary sensor dynamically through discovery."""

    @callback
    def async_discover(tasmota_entity, discovery_hash):
        """Discover and add a Tasmota binary sensor."""
        async_add_entities(
            [
                TasmotaBinarySensor(
                    tasmota_entity=tasmota_entity, discovery_hash=discovery_hash
                )
            ]
        )

    opp.data[
        DATA_REMOVE_DISCOVER_COMPONENT.format(binary_sensor.DOMAIN)
    ] = async_dispatcher_connect(
        opp,
        TASMOTA_DISCOVERY_ENTITY_NEW.format(binary_sensor.DOMAIN),
        async_discover,
    )


class TasmotaBinarySensor(
    TasmotaAvailability,
    TasmotaDiscoveryUpdate,
    BinarySensorEntity,
):
    """Representation a Tasmota binary sensor."""

    def __init__(self, **kwds):
        """Initialize the Tasmota binary sensor."""
        self._delay_listener = None
        self._state = None

        super().__init__(
            **kwds,
        )

    @callback
    def off_delay_listener(self, now):
        """Switch device off after a delay."""
        self._delay_listener = None
        self._state = False
        self.async_write_op_state()

    @callback
    def state_updated(self, state, **kwargs):
        """Handle state updates."""
        self._state = state

        if self._delay_listener is not None:
            self._delay_listener()
            self._delay_listener = None

        off_delay = self._tasmota_entity.off_delay
        if self._state and off_delay is not None:
            self._delay_listener = evt.async_call_later(
                self.opp, off_delay, self.off_delay_listener
            )

        self.async_write_op_state()

    @property
    def force_update(self):
        """Force update."""
        return True

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state
