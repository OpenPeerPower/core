"""The nexia integration base entity."""

from openpeerpower.const import ATTR_ATTRIBUTION
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    DOMAIN,
    MANUFACTURER,
    SIGNAL_THERMOSTAT_UPDATE,
    SIGNAL_ZONE_UPDATE,
)


class NexiaEntity(CoordinatorEntity):
    """Base class for nexia entities."""

    def __init__(self, coordinator, name, unique_id):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }


class NexiaThermostatEntity(NexiaEntity):
    """Base class for nexia devices attached to a thermostat."""

    def __init__(self, coordinator, thermostat, name, unique_id):
        """Initialize the entity."""
        super().__init__(coordinator, name, unique_id)
        self._thermostat = thermostat

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self._thermostat.thermostat_id)},
            "name": self._thermostat.get_name(),
            "model": self._thermostat.get_model(),
            "sw_version": self._thermostat.get_firmware(),
            "manufacturer": MANUFACTURER,
        }

    async def async_added_to_opp(self):
        """Listen for signals for services."""
        await super().async_added_to_opp()
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{SIGNAL_THERMOSTAT_UPDATE}-{self._thermostat.thermostat_id}",
                self.async_write_op_state,
            )
        )


class NexiaThermostatZoneEntity(NexiaThermostatEntity):
    """Base class for nexia devices attached to a thermostat."""

    def __init__(self, coordinator, zone, name, unique_id):
        """Initialize the entity."""
        super().__init__(coordinator, zone.thermostat, name, unique_id)
        self._zone = zone

    @property
    def device_info(self):
        """Return the device_info of the device."""
        data = super().device_info
        zone_name = self._zone.get_name()
        data.update(
            {
                "identifiers": {(DOMAIN, self._zone.zone_id)},
                "name": zone_name,
                "suggested_area": zone_name,
                "via_device": (DOMAIN, self._zone.thermostat.thermostat_id),
            }
        )
        return data

    async def async_added_to_opp(self):
        """Listen for signals for services."""
        await super().async_added_to_opp()
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{SIGNAL_ZONE_UPDATE}-{self._zone.zone_id}",
                self.async_write_op_state,
            )
        )
