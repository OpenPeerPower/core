"""Binary sensor platform support for wiffi devices."""

from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from . import WiffiEntity
from .const import CREATE_ENTITY_SIGNAL


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up platform for a new integration.

    Called by the OPP framework after async_forward_entry_setup has been called
    during initialization of a new integration (= wiffi).
    """

    @callback
    def _create_entity(device, metric):
        """Create platform specific entities."""
        entities = []

        if metric.is_bool:
            entities.append(BoolEntity(device, metric, config_entry.options))

        async_add_entities(entities)

    async_dispatcher_connect(opp, CREATE_ENTITY_SIGNAL, _create_entity)


class BoolEntity(WiffiEntity, BinarySensorEntity):
    """Entity for wiffi metrics which have a boolean value."""

    def __init__(self, device, metric, options):
        """Initialize the entity."""
        super().__init__(device, metric, options)
        self._value = metric.value
        self.reset_expiration_date()

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._value

    @callback
    def _update_value_callback(self, device, metric):
        """Update the value of the entity.

        Called if a new message has been received from the wiffi device.
        """
        self.reset_expiration_date()
        self._value = metric.value
        self.async_write_op_state()
