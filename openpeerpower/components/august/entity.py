"""Base class for August entity."""
from openpeerpower.core import callback
from openpeerpower.helpers.entity import Entity

from . import DOMAIN
from .const import MANUFACTURER


class AugustEntityMixin(Entity):
    """Base implementation for August device."""

    def __init__(self, data, device):
        """Initialize an August device."""
        super().__init__()
        self._data = data
        self._device = device

    @property
    def should_poll(self):
        """Return False, updates are controlled via the hub."""
        return False

    @property
    def _device_id(self):
        return self._device.device_id

    @property
    def _detail(self):
        return self._data.get_device_detail(self._device.device_id)

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device.device_name,
            "manufacturer": MANUFACTURER,
            "sw_version": self._detail.firmware_version,
            "model": self._detail.model,
        }

    @callback
    def _update_from_data_and_write_state(self):
        self._update_from_data()
        self.async_write_op_state()

    async def async_added_to_opp(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._data.async_subscribe_device_id(
                self._device_id, self._update_from_data_and_write_state
            )
        )
        self.async_on_remove(
            self._data.activity_stream.async_subscribe_device_id(
                self._device_id, self._update_from_data_and_write_state
            )
        )
