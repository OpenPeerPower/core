"""Support for SimpliSafe alarm control panels."""
import re

from simplipy.errors import SimplipyError
from simplipy.system import SystemStates

from openpeerpower.components.alarm_control_panel import (
    FORMAT_NUMBER,
    FORMAT_TEXT,
    AlarmControlPanelEntity,
)
from openpeerpower.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from openpeerpower.const import (
    CONF_CODE,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from openpeerpower.core import callback

from . import SimpliSafeEntity
from .const import (
    ATTR_ALARM_DURATION,
    ATTR_ALARM_VOLUME,
    ATTR_CHIME_VOLUME,
    ATTR_ENTRY_DELAY_AWAY,
    ATTR_ENTRY_DELAY_HOME,
    ATTR_EXIT_DELAY_AWAY,
    ATTR_EXIT_DELAY_HOME,
    ATTR_LIGHT,
    ATTR_VOICE_PROMPT_VOLUME,
    DATA_CLIENT,
    DOMAIN,
    LOGGER,
    VOLUME_STRING_MAP,
)

ATTR_BATTERY_BACKUP_POWER_LEVEL = "battery_backup_power_level"
ATTR_GSM_STRENGTH = "gsm_strength"
ATTR_PIN_NAME = "pin_name"
ATTR_RF_JAMMING = "rf_jamming"
ATTR_WALL_POWER_LEVEL = "wall_power_level"
ATTR_WIFI_STRENGTH = "wifi_strength"


async def async_setup_entry(opp, entry, async_add_entities):
    """Set up a SimpliSafe alarm control panel based on a config entry."""
    simplisafe = opp.data[DOMAIN][DATA_CLIENT][entry.entry_id]
    async_add_entities(
        [SimpliSafeAlarm(simplisafe, system) for system in simplisafe.systems.values()],
        True,
    )


class SimpliSafeAlarm(SimpliSafeEntity, AlarmControlPanelEntity):
    """Representation of a SimpliSafe alarm."""

    def __init__(self, simplisafe, system):
        """Initialize the SimpliSafe alarm."""
        super().__init__(simplisafe, system, "Alarm Control Panel")
        self._changed_by = None
        self._last_event = None

        if system.alarm_going_off:
            self._state = STATE_ALARM_TRIGGERED
        elif system.state == SystemStates.away:
            self._state = STATE_ALARM_ARMED_AWAY
        elif system.state in (
            SystemStates.away_count,
            SystemStates.exit_delay,
            SystemStates.home_count,
        ):
            self._state = STATE_ALARM_ARMING
        elif system.state == SystemStates.home:
            self._state = STATE_ALARM_ARMED_HOME
        elif system.state == SystemStates.off:
            self._state = STATE_ALARM_DISARMED
        else:
            self._state = None

    @property
    def changed_by(self):
        """Return info about who changed the alarm last."""
        return self._changed_by

    @property
    def code_format(self):
        """Return one or more digits/characters."""
        if not self._simplisafe.config_entry.options.get(CONF_CODE):
            return None
        if isinstance(
            self._simplisafe.config_entry.options[CONF_CODE], str
        ) and re.search("^\\d+$", self._simplisafe.config_entry.options[CONF_CODE]):
            return FORMAT_NUMBER
        return FORMAT_TEXT

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    @callback
    def _is_code_valid(self, code, state):
        """Validate that a code matches the required one."""
        if not self._simplisafe.config_entry.options.get(CONF_CODE):
            return True

        if not code or code != self._simplisafe.config_entry.options[CONF_CODE]:
            LOGGER.warning(
                "Incorrect alarm code entered (target state: %s): %s", state, code
            )
            return False

        return True

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        if not self._is_code_valid(code, STATE_ALARM_DISARMED):
            return

        try:
            await self._system.set_off()
        except SimplipyError as err:
            LOGGER.error('Error while disarming "%s": %s', self._system.system_id, err)
            return

        self._state = STATE_ALARM_DISARMED
        self.async_write_op_state()

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        if not self._is_code_valid(code, STATE_ALARM_ARMED_HOME):
            return

        try:
            await self._system.set_home()
        except SimplipyError as err:
            LOGGER.error(
                'Error while arming "%s" (home): %s', self._system.system_id, err
            )
            return

        self._state = STATE_ALARM_ARMED_HOME
        self.async_write_op_state()

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        if not self._is_code_valid(code, STATE_ALARM_ARMED_AWAY):
            return

        try:
            await self._system.set_away()
        except SimplipyError as err:
            LOGGER.error(
                'Error while arming "%s" (away): %s', self._system.system_id, err
            )
            return

        self._state = STATE_ALARM_ARMING
        self.async_write_op_state()

    @callback
    def async_update_from_rest_api(self):
        """Update the entity with the provided REST API data."""
        if self._system.version == 3:
            self._attrs.update(
                {
                    ATTR_ALARM_DURATION: self._system.alarm_duration,
                    ATTR_ALARM_VOLUME: VOLUME_STRING_MAP[self._system.alarm_volume],
                    ATTR_BATTERY_BACKUP_POWER_LEVEL: self._system.battery_backup_power_level,
                    ATTR_CHIME_VOLUME: VOLUME_STRING_MAP[self._system.chime_volume],
                    ATTR_ENTRY_DELAY_AWAY: self._system.entry_delay_away,
                    ATTR_ENTRY_DELAY_HOME: self._system.entry_delay_home,
                    ATTR_EXIT_DELAY_AWAY: self._system.exit_delay_away,
                    ATTR_EXIT_DELAY_HOME: self._system.exit_delay_home,
                    ATTR_GSM_STRENGTH: self._system.gsm_strength,
                    ATTR_LIGHT: self._system.light,
                    ATTR_RF_JAMMING: self._system.rf_jamming,
                    ATTR_VOICE_PROMPT_VOLUME: VOLUME_STRING_MAP[
                        self._system.voice_prompt_volume
                    ],
                    ATTR_WALL_POWER_LEVEL: self._system.wall_power_level,
                    ATTR_WIFI_STRENGTH: self._system.wifi_strength,
                }
            )

        # Although system state updates are designed the come via the websocket, the
        # SimpliSafe cloud can sporadically fail to send those updates as expected; so,
        # just in case, we synchronize the state via the REST API, too:
        if self._system.state == SystemStates.alarm:
            self._state = STATE_ALARM_TRIGGERED
        elif self._system.state == SystemStates.away:
            self._state = STATE_ALARM_ARMED_AWAY
        elif self._system.state in (SystemStates.away_count, SystemStates.exit_delay):
            self._state = STATE_ALARM_ARMING
        elif self._system.state == SystemStates.home:
            self._state = STATE_ALARM_ARMED_HOME
        elif self._system.state == SystemStates.off:
            self._state = STATE_ALARM_DISARMED
        else:
            self._state = None
