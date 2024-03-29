"""Binary Sensor platform for FireServiceRota integration."""
from openpeerpower.components.binary_sensor import BinarySensorEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN as FIRESERVICEROTA_DOMAIN


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up FireServiceRota binary sensor based on a config entry."""

    client = opp.data[FIRESERVICEROTA_DOMAIN][entry.entry_id][DATA_CLIENT]

    coordinator: DataUpdateCoordinator = opp.data[FIRESERVICEROTA_DOMAIN][
        entry.entry_id
    ][DATA_COORDINATOR]

    async_add_entities([ResponseBinarySensor(coordinator, client, entry)])


class ResponseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an FireServiceRota sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, client, entry):
        """Initialize."""
        super().__init__(coordinator)
        self._client = client
        self._unique_id = f"{entry.unique_id}_Duty"

        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Duty"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._state:
            return "mdi:calendar-check"

        return "mdi:calendar-remove"

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this binary sensor."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""

        self._state = self._client.on_duty

        return self._state

    @property
    def extra_state_attributes(self):
        """Return available attributes for binary sensor."""
        attr = {}
        if not self.coordinator.data:
            return attr

        data = self.coordinator.data
        attr = {
            key: data[key]
            for key in (
                "start_time",
                "end_time",
                "available",
                "active",
                "assigned_function_ids",
                "skill_ids",
                "type",
                "assigned_function",
            )
            if key in data
        }

        return attr
