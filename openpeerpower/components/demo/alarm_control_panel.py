"""Demo platform that has two fake alarm control panels."""
import datetime

from openpeerpower.components.manual.alarm_control_panel import ManualAlarm
from openpeerpower.const import (
    CONF_ARMING_TIME,
    CONF_DELAY_TIME,
    CONF_TRIGGER_TIME,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the Demo alarm control panel platform."""
    async_add_entities(
        [
            ManualAlarm(
                opp,
                "Alarm",
                "1234",
                None,
                True,
                False,
                {
                    STATE_ALARM_ARMED_AWAY: {
                        CONF_ARMING_TIME: datetime.timedelta(seconds=5),
                        CONF_DELAY_TIME: datetime.timedelta(seconds=0),
                        CONF_TRIGGER_TIME: datetime.timedelta(seconds=10),
                    },
                    STATE_ALARM_ARMED_HOME: {
                        CONF_ARMING_TIME: datetime.timedelta(seconds=5),
                        CONF_DELAY_TIME: datetime.timedelta(seconds=0),
                        CONF_TRIGGER_TIME: datetime.timedelta(seconds=10),
                    },
                    STATE_ALARM_ARMED_NIGHT: {
                        CONF_ARMING_TIME: datetime.timedelta(seconds=5),
                        CONF_DELAY_TIME: datetime.timedelta(seconds=0),
                        CONF_TRIGGER_TIME: datetime.timedelta(seconds=10),
                    },
                    STATE_ALARM_DISARMED: {
                        CONF_DELAY_TIME: datetime.timedelta(seconds=0),
                        CONF_TRIGGER_TIME: datetime.timedelta(seconds=10),
                    },
                    STATE_ALARM_ARMED_CUSTOM_BYPASS: {
                        CONF_ARMING_TIME: datetime.timedelta(seconds=5),
                        CONF_DELAY_TIME: datetime.timedelta(seconds=0),
                        CONF_TRIGGER_TIME: datetime.timedelta(seconds=10),
                    },
                    STATE_ALARM_TRIGGERED: {
                        CONF_ARMING_TIME: datetime.timedelta(seconds=5)
                    },
                },
            )
        ]
    )


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up the Demo config entry."""
    await async_setup_platform(opp, {}, async_add_entities)
