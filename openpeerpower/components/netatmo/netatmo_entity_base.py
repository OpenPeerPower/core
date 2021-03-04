"""Base class for Netatmo entities."""
import logging
from typing import Dict, List

from openpeerpower.core import CALLBACK_TYPE, callback
from openpeerpower.helpers.entity import Entity

from .const import DATA_DEVICE_IDS, DOMAIN, MANUFACTURER, MODELS, SIGNAL_NAME
from .data_handler import NetatmoDataHandler

_LOGGER = logging.getLogger(__name__)


class NetatmoBase(Entity):
    """Netatmo entity base class."""

    def __init__(self, data_handler: NetatmoDataHandler) -> None:
        """Set up Netatmo entity base."""
        self.data_handler = data_handler
        self._data_classes: List[Dict] = []
        self._listeners: List[CALLBACK_TYPE] = []

        self._device_name = None
        self._id = None
        self._model = None
        self._name = None
        self._unique_id = None

    async def async_added_to_opp(self) -> None:
        """Entity created."""
        _LOGGER.debug("New client %s", self.entity_id)
        for data_class in self._data_classes:
            signal_name = data_class[SIGNAL_NAME]

            if "home_id" in data_class:
                await self.data_handler.register_data_class(
                    data_class["name"],
                    signal_name,
                    self.async_update_callback,
                    home_id=data_class["home_id"],
                )

            elif data_class["name"] == "PublicData":
                await self.data_handler.register_data_class(
                    data_class["name"],
                    signal_name,
                    self.async_update_callback,
                    lat_ne=data_class["lat_ne"],
                    lon_ne=data_class["lon_ne"],
                    lat_sw=data_class["lat_sw"],
                    lon_sw=data_class["lon_sw"],
                )

            else:
                await self.data_handler.register_data_class(
                    data_class["name"], signal_name, self.async_update_callback
                )

            await self.data_handler.unregister_data_class(signal_name, None)

        registry = await self.opp.helpers.device_registry.async_get_registry()
        device = registry.async_get_device({(DOMAIN, self._id)}, set())
        self.opp.data[DOMAIN][DATA_DEVICE_IDS][self._id] = device.id

        self.async_update_callback()

    async def async_will_remove_from_opp(self):
        """Run when entity will be removed from opp."""
        await super().async_will_remove_from_opp()

        for listener in self._listeners:
            listener()

        for data_class in self._data_classes:
            await self.data_handler.unregister_data_class(
                data_class[SIGNAL_NAME], self.async_update_callback
            )

    @callback
    def async_update_callback(self):
        """Update the entity's state."""
        raise NotImplementedError

    @property
    def _data(self):
        """Return data for this entity."""
        return self.data_handler.data[self._data_classes[0]["name"]]

    @property
    def unique_id(self):
        """Return the unique ID of this entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of this entity."""
        return self._name

    @property
    def device_info(self):
        """Return the device info for the sensor."""
        return {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": MODELS[self._model],
        }
