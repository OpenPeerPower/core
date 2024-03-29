"""Support for August lock."""
import logging

from yalexs.activity import SOURCE_PUBNUB, ActivityType
from yalexs.lock import LockStatus
from yalexs.util import update_lock_detail_from_activity

from openpeerpower.components.lock import ATTR_CHANGED_BY, LockEntity
from openpeerpower.const import ATTR_BATTERY_LEVEL
from openpeerpower.core import callback
from openpeerpower.helpers.restore_state import RestoreEntity

from .const import DATA_AUGUST, DOMAIN
from .entity import AugustEntityMixin

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up August locks."""
    data = opp.data[DOMAIN][config_entry.entry_id][DATA_AUGUST]
    async_add_entities([AugustLock(data, lock) for lock in data.locks])


class AugustLock(AugustEntityMixin, RestoreEntity, LockEntity):
    """Representation of an August lock."""

    def __init__(self, data, device):
        """Initialize the lock."""
        super().__init__(data, device)
        self._data = data
        self._device = device
        self._lock_status = None
        self._changed_by = None
        self._available = False
        self._update_from_data()

    async def async_lock(self, **kwargs):
        """Lock the device."""
        await self._call_lock_operation(self._data.async_lock)

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        await self._call_lock_operation(self._data.async_unlock)

    async def _call_lock_operation(self, lock_operation):
        activities = await lock_operation(self._device_id)
        for lock_activity in activities:
            update_lock_detail_from_activity(self._detail, lock_activity)

        if self._update_lock_status_from_detail():
            _LOGGER.debug(
                "async_signal_device_id_update (from lock operation): %s",
                self._device_id,
            )
            self._data.async_signal_device_id_update(self._device_id)

    def _update_lock_status_from_detail(self):
        self._available = self._detail.bridge_is_online

        if self._lock_status != self._detail.lock_status:
            self._lock_status = self._detail.lock_status
            return True
        return False

    @callback
    def _update_from_data(self):
        """Get the latest state of the sensor and update activity."""
        lock_activity = self._data.activity_stream.get_latest_device_activity(
            self._device_id,
            {ActivityType.LOCK_OPERATION, ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR},
        )

        if lock_activity is not None:
            self._changed_by = lock_activity.operated_by
            update_lock_detail_from_activity(self._detail, lock_activity)
            # If the source is pubnub the lock must be online since its a live update
            if lock_activity.source == SOURCE_PUBNUB:
                self._detail.set_online(True)

        bridge_activity = self._data.activity_stream.get_latest_device_activity(
            self._device_id, {ActivityType.BRIDGE_OPERATION}
        )

        if bridge_activity is not None:
            update_lock_detail_from_activity(self._detail, bridge_activity)

        self._update_lock_status_from_detail()

    @property
    def name(self):
        """Return the name of this device."""
        return self._device.device_name

    @property
    def available(self):
        """Return the availability of this sensor."""
        return self._available

    @property
    def is_locked(self):
        """Return true if device is on."""
        if self._lock_status is None or self._lock_status is LockStatus.UNKNOWN:
            return None
        return self._lock_status is LockStatus.LOCKED

    @property
    def changed_by(self):
        """Last change triggered by."""
        return self._changed_by

    @property
    def extra_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {ATTR_BATTERY_LEVEL: self._detail.battery_level}

        if self._detail.keypad is not None:
            attributes["keypad_battery_level"] = self._detail.keypad.battery_level

        return attributes

    async def async_added_to_opp(self):
        """Restore ATTR_CHANGED_BY on startup since it is likely no longer in the activity log."""
        await super().async_added_to_opp()

        last_state = await self.async_get_last_state()
        if not last_state:
            return

        if ATTR_CHANGED_BY in last_state.attributes:
            self._changed_by = last_state.attributes[ATTR_CHANGED_BY]

    @property
    def unique_id(self) -> str:
        """Get the unique id of the lock."""
        return f"{self._device_id:s}_lock"
