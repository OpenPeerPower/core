"""Class to hold all lock accessories."""
import logging

from pyhap.const import CATEGORY_DOOR_LOCK

from openpeerpower.components.lock import DOMAIN, STATE_LOCKED, STATE_UNLOCKED
from openpeerpower.const import ATTR_CODE, ATTR_ENTITY_ID, STATE_UNKNOWN
from openpeerpower.core import callback

from .accessories import TYPES, HomeAccessory
from .const import CHAR_LOCK_CURRENT_STATE, CHAR_LOCK_TARGET_STATE, SERV_LOCK

_LOGGER = logging.getLogger(__name__)

OPP_TO_HOMEKIT = {
    STATE_UNLOCKED: 0,
    STATE_LOCKED: 1,
    # Value 2 is Jammed which opp doesn't have a state for
    STATE_UNKNOWN: 3,
}

HOMEKIT_TO_OPP = {c: s for s, c in OPP_TO_HOMEKIT.items()}

STATE_TO_SERVICE = {STATE_LOCKED: "lock", STATE_UNLOCKED: "unlock"}


@TYPES.register("Lock")
class Lock(HomeAccessory):
    """Generate a Lock accessory for a lock entity.

    The lock entity must support: unlock and lock.
    """

    def __init__(self, *args):
        """Initialize a Lock accessory object."""
        super().__init__(*args, category=CATEGORY_DOOR_LOCK)
        self._code = self.config.get(ATTR_CODE)
        state = self.opp.states.get(self.entity_id)

        serv_lock_mechanism = self.add_preload_service(SERV_LOCK)
        self.char_current_state = serv_lock_mechanism.configure_char(
            CHAR_LOCK_CURRENT_STATE, value=OPP_TO_HOMEKIT[STATE_UNKNOWN]
        )
        self.char_target_state = serv_lock_mechanism.configure_char(
            CHAR_LOCK_TARGET_STATE,
            value=OPP_TO_HOMEKIT[STATE_LOCKED],
            setter_callback=self.set_state,
        )
        self.async_update_state(state)

    def set_state(self, value):
        """Set lock state to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set state to %d", self.entity_id, value)

        opp_value = HOMEKIT_TO_OPP.get(value)
        service = STATE_TO_SERVICE[opp_value]

        if self.char_current_state.value != value:
            self.char_current_state.set_value(value)

        params = {ATTR_ENTITY_ID: self.entity_id}
        if self._code:
            params[ATTR_CODE] = self._code
        self.async_call_service(DOMAIN, service, params)

    @callback
    def async_update_state(self, new_state):
        """Update lock after state changed."""
        opp_state = new_state.state
        if opp_state in OPP_TO_HOMEKIT:
            current_lock_state = OPP_TO_HOMEKIT[opp_state]
            _LOGGER.debug(
                "%s: Updated current state to %s (%d)",
                self.entity_id,
                opp_state,
                current_lock_state,
            )
            # LockTargetState only supports locked and unlocked
            # Must set lock target state before current state
            # or there will be no notification
            if opp_state in (STATE_LOCKED, STATE_UNLOCKED):
                if self.char_target_state.value != current_lock_state:
                    self.char_target_state.set_value(current_lock_state)

            # Set lock current state ONLY after ensuring that
            # target state is correct or there will be no
            # notification
            if self.char_current_state.value != current_lock_state:
                self.char_current_state.set_value(current_lock_state)
