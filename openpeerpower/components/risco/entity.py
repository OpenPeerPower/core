"""A risco entity base class."""
from openpeerpower.helpers.update_coordinator import CoordinatorEntity


def binary_sensor_unique_id(risco, zone_id):
    """Return unique id for the binary sensor."""
    return f"{risco.site_uuid}_zone_{zone_id}"


class RiscoEntity(CoordinatorEntity):
    """Risco entity base class."""

    def _get_data_from_coordinator(self):
        raise NotImplementedError

    def _refresh_from_coordinator(self):
        self._get_data_from_coordinator()
        self.async_write_op_state()

    async def async_added_to_opp(self):
        """When entity is added to opp."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._refresh_from_coordinator)
        )

    @property
    def _risco(self):
        """Return the Risco API object."""
        return self.coordinator.risco
