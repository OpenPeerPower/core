"""Support for SimpliSafe locks."""
from simplipy.errors import SimplipyError
from simplipy.lock import LockStates

from openpeerpower.components.lock import LockEntity
from openpeerpower.core import callback

from . import SimpliSafeEntity
from .const import DATA_CLIENT, DOMAIN, LOGGER

ATTR_LOCK_LOW_BATTERY = "lock_low_battery"
ATTR_JAMMED = "jammed"
ATTR_PIN_PAD_LOW_BATTERY = "pin_pad_low_battery"


async def async_setup_entry(opp, entry, async_add_entities):
    """Set up SimpliSafe locks based on a config entry."""
    simplisafe = opp.data[DOMAIN][DATA_CLIENT][entry.entry_id]
    locks = []

    for system in simplisafe.systems.values():
        if system.version == 2:
            LOGGER.info("Skipping lock setup for V2 system: %s", system.system_id)
            continue

        for lock in system.locks.values():
            locks.append(SimpliSafeLock(simplisafe, system, lock))

    async_add_entities(locks)


class SimpliSafeLock(SimpliSafeEntity, LockEntity):
    """Define a SimpliSafe lock."""

    def __init__(self, simplisafe, system, lock):
        """Initialize."""
        super().__init__(simplisafe, system, lock.name, serial=lock.serial)
        self._lock = lock
        self._is_locked = None

    @property
    def is_locked(self):
        """Return true if the lock is locked."""
        return self._is_locked

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        try:
            await self._lock.lock()
        except SimplipyError as err:
            LOGGER.error('Error while locking "%s": %s', self._lock.name, err)
            return

        self._is_locked = True
        self.async_write_op_state()

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        try:
            await self._lock.unlock()
        except SimplipyError as err:
            LOGGER.error('Error while unlocking "%s": %s', self._lock.name, err)
            return

        self._is_locked = False
        self.async_write_op_state()

    @callback
    def async_update_from_rest_api(self):
        """Update the entity with the provided REST API data."""
        self._attrs.update(
            {
                ATTR_LOCK_LOW_BATTERY: self._lock.lock_low_battery,
                ATTR_JAMMED: self._lock.state == LockStates.jammed,
                ATTR_PIN_PAD_LOW_BATTERY: self._lock.pin_pad_low_battery,
            }
        )

        self._is_locked = self._lock.state == LockStates.locked
