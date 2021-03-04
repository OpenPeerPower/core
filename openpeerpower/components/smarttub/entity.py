"""SmartTub integration."""
import logging

import smarttub

from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .helpers import get_spa_name

_LOGGER = logging.getLogger(__name__)


class SmartTubEntity(CoordinatorEntity):
    """Base class for SmartTub entities."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, spa: smarttub.Spa, entity_type
    ):
        """Initialize the entity.

        Given a spa id and a short name for the entity, we provide basic device
        info, name, unique id, etc. for all derived entities.
        """

        super().__init__(coordinator)
        self.spa = spa
        self._entity_type = entity_type

    @property
    def unique_id(self) -> str:
        """Return a unique id for the entity."""
        return f"{self.spa.id}-{self._entity_type}"

    @property
    def device_info(self) -> str:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.spa.id)},
            "manufacturer": self.spa.brand,
            "model": self.spa.model,
        }

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        spa_name = get_spa_name(self.spa)
        return f"{spa_name} {self._entity_type}"

    @property
    def spa_status(self) -> smarttub.SpaState:
        """Retrieve the result of Spa.get_status()."""

        return self.coordinator.data[self.spa.id].get("status")


class SmartTubSensorBase(SmartTubEntity):
    """Base class for SmartTub sensors."""

    def __init__(self, coordinator, spa, sensor_name, attr_name):
        """Initialize the entity."""
        super().__init__(coordinator, spa, sensor_name)
        self._attr_name = attr_name

    @property
    def _state(self):
        """Retrieve the underlying state from the spa."""
        return getattr(self.spa_status, self._attr_name)
