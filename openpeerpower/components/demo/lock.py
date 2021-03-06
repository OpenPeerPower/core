"""Demo lock platform that has two fake locks."""
from openpeerpower.components.lock import SUPPORT_OPEN, LockEntity
from openpeerpower.const import STATE_LOCKED, STATE_UNLOCKED


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Demo lock platform."""
    async_add_entities(
        [
            DemoLock("Front Door", STATE_LOCKED),
            DemoLock("Kitchen Door", STATE_UNLOCKED),
            DemoLock("Openable Lock", STATE_LOCKED, True),
        ]
    )


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Demo config entry."""
    await async_setup_platform(opp, {}, async_add_entities)


class DemoLock(LockEntity):
    """Representation of a Demo lock."""

    def __init__(self, name, state, openable=False):
        """Initialize the lock."""
        self._name = name
        self._state = state
        self._openable = openable

    @property
    def should_poll(self):
        """No polling needed for a demo lock."""
        return False

    @property
    def name(self):
        """Return the name of the lock if any."""
        return self._name

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        return self._state == STATE_LOCKED

    def lock(self, **kwargs):
        """Lock the device."""
        self._state = STATE_LOCKED
        self.schedule_update_op_state()

    def unlock(self, **kwargs):
        """Unlock the device."""
        self._state = STATE_UNLOCKED
        self.schedule_update_op_state()

    def open(self, **kwargs):
        """Open the door latch."""
        self._state = STATE_UNLOCKED
        self.schedule_update_op_state()

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._openable:
            return SUPPORT_OPEN
