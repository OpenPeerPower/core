"""Support for Smart Meter Texas sensors."""
from smart_meter_texas import Meter

from openpeerpower.const import CONF_ADDRESS, ENERGY_KILO_WATT_HOUR
from openpeerpower.core import callback
from openpeerpower.helpers.restore_state import RestoreEntity
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DATA_COORDINATOR,
    DATA_SMART_METER,
    DOMAIN,
    ELECTRIC_METER,
    ESIID,
    METER_NUMBER,
)


async def async_setup_entry.opp, config_entry, async_add_entities):
    """Set up the Smart Meter Texas sensors."""
    coordinator = opp.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    meters = opp.data[DOMAIN][config_entry.entry_id][DATA_SMART_METER].meters

    async_add_entities(
        [SmartMeterTexasSensor(meter, coordinator) for meter in meters], False
    )


class SmartMeterTexasSensor(CoordinatorEntity, RestoreEntity):
    """Representation of an Smart Meter Texas sensor."""

    def __init__(self, meter: Meter, coordinator: DataUpdateCoordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.meter = meter
        self._state = None
        self._available = False

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ENERGY_KILO_WATT_HOUR

    @property
    def name(self):
        """Device Name."""
        return f"{ELECTRIC_METER} {self.meter.meter}"

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return f"{self.meter.esiid}_{self.meter.meter}"

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def state(self):
        """Get the latest reading."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {
            METER_NUMBER: self.meter.meter,
            ESIID: self.meter.esiid,
            CONF_ADDRESS: self.meter.address,
        }
        return attributes

    @callback
    def _state_update(self):
        """Call when the coordinator has an update."""
        self._available = self.coordinator.last_update_success
        if self._available:
            self._state = self.meter.reading
        self.async_write_op_state()

    async def async_added_to.opp(self):
        """Subscribe to updates."""
        self.async_on_remove(self.coordinator.async_add_listener(self._state_update))

        # If the background update finished before
        # we added the entity, there is no need to restore
        # state.
        if self.coordinator.last_update_success:
            return

        last_state = await self.async_get_last_state()
        if last_state:
            self._state = last_state.state
            self._available = True
