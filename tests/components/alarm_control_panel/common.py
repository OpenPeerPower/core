"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.alarm_control_panel import DOMAIN
from openpeerpower.const import (
    ATTR_CODE,
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_CUSTOM_BYPASS,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    SERVICE_ALARM_TRIGGER,
)


async def async_alarm_disarm(opp, code=None, entity_id=ENTITY_MATCH_ALL):
    """Send the alarm the command for disarm."""
    data = {}
    if code:
        data[ATTR_CODE] = code
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_ALARM_DISARM, data, blocking=True)


async def async_alarm_arm_home(opp, code=None, entity_id=ENTITY_MATCH_ALL):
    """Send the alarm the command for disarm."""
    data = {}
    if code:
        data[ATTR_CODE] = code
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_ALARM_ARM_HOME, data, blocking=True)


async def async_alarm_arm_away(opp, code=None, entity_id=ENTITY_MATCH_ALL):
    """Send the alarm the command for disarm."""
    data = {}
    if code:
        data[ATTR_CODE] = code
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_ALARM_ARM_AWAY, data, blocking=True)


async def async_alarm_arm_night(opp, code=None, entity_id=ENTITY_MATCH_ALL):
    """Send the alarm the command for disarm."""
    data = {}
    if code:
        data[ATTR_CODE] = code
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_ALARM_ARM_NIGHT, data, blocking=True)


async def async_alarm_trigger(opp, code=None, entity_id=ENTITY_MATCH_ALL):
    """Send the alarm the command for disarm."""
    data = {}
    if code:
        data[ATTR_CODE] = code
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_ALARM_TRIGGER, data, blocking=True)


async def async_alarm_arm_custom_bypass(opp, code=None, entity_id=ENTITY_MATCH_ALL):
    """Send the alarm the command for disarm."""
    data = {}
    if code:
        data[ATTR_CODE] = code
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(
        DOMAIN, SERVICE_ALARM_ARM_CUSTOM_BYPASS, data, blocking=True
    )
