"""Provides device automations for Philips Hue events."""
import voluptuous as vol

from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from openpeerpower.components.openpeerpower.triggers import event as event_trigger
from openpeerpower.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
    CONF_UNIQUE_ID,
)

from . import DOMAIN
from .hue_event import CONF_HUE_EVENT

CONF_SUBTYPE = "subtype"

CONF_SHORT_PRESS = "remote_button_short_press"
CONF_SHORT_RELEASE = "remote_button_short_release"
CONF_LONG_RELEASE = "remote_button_long_release"
CONF_DOUBLE_SHORT_RELEASE = "remote_double_button_short_press"
CONF_DOUBLE_LONG_RELEASE = "remote_double_button_long_press"

CONF_TURN_ON = "turn_on"
CONF_TURN_OFF = "turn_off"
CONF_DIM_UP = "dim_up"
CONF_DIM_DOWN = "dim_down"
CONF_BUTTON_1 = "button_1"
CONF_BUTTON_2 = "button_2"
CONF_BUTTON_3 = "button_3"
CONF_BUTTON_4 = "button_4"
CONF_DOUBLE_BUTTON_1 = "double_buttons_1_3"
CONF_DOUBLE_BUTTON_2 = "double_buttons_2_4"

HUE_DIMMER_REMOTE_MODEL = "Hue dimmer switch"  # RWL020/021
HUE_DIMMER_REMOTE = {
    (CONF_SHORT_RELEASE, CONF_TURN_ON): {CONF_EVENT: 1002},
    (CONF_LONG_RELEASE, CONF_TURN_ON): {CONF_EVENT: 1003},
    (CONF_SHORT_RELEASE, CONF_DIM_UP): {CONF_EVENT: 2002},
    (CONF_LONG_RELEASE, CONF_DIM_UP): {CONF_EVENT: 2003},
    (CONF_SHORT_RELEASE, CONF_DIM_DOWN): {CONF_EVENT: 3002},
    (CONF_LONG_RELEASE, CONF_DIM_DOWN): {CONF_EVENT: 3003},
    (CONF_SHORT_RELEASE, CONF_TURN_OFF): {CONF_EVENT: 4002},
    (CONF_LONG_RELEASE, CONF_TURN_OFF): {CONF_EVENT: 4003},
}

HUE_BUTTON_REMOTE_MODEL = "Hue Smart button"  # ZLLSWITCH/ROM001
HUE_BUTTON_REMOTE = {
    (CONF_SHORT_RELEASE, CONF_TURN_ON): {CONF_EVENT: 1002},
    (CONF_LONG_RELEASE, CONF_TURN_ON): {CONF_EVENT: 1003},
}

HUE_TAP_REMOTE_MODEL = "Hue tap switch"  # ZGPSWITCH
HUE_TAP_REMOTE = {
    (CONF_SHORT_PRESS, CONF_BUTTON_1): {CONF_EVENT: 34},
    (CONF_SHORT_PRESS, CONF_BUTTON_2): {CONF_EVENT: 16},
    (CONF_SHORT_PRESS, CONF_BUTTON_3): {CONF_EVENT: 17},
    (CONF_SHORT_PRESS, CONF_BUTTON_4): {CONF_EVENT: 18},
}

HUE_FOHSWITCH_REMOTE_MODEL = "Friends of Hue Switch"  # ZGPSWITCH
HUE_FOHSWITCH_REMOTE = {
    (CONF_SHORT_PRESS, CONF_BUTTON_1): {CONF_EVENT: 20},
    (CONF_LONG_RELEASE, CONF_BUTTON_1): {CONF_EVENT: 16},
    (CONF_SHORT_PRESS, CONF_BUTTON_2): {CONF_EVENT: 21},
    (CONF_LONG_RELEASE, CONF_BUTTON_2): {CONF_EVENT: 17},
    (CONF_SHORT_PRESS, CONF_BUTTON_3): {CONF_EVENT: 23},
    (CONF_LONG_RELEASE, CONF_BUTTON_3): {CONF_EVENT: 19},
    (CONF_SHORT_PRESS, CONF_BUTTON_4): {CONF_EVENT: 22},
    (CONF_LONG_RELEASE, CONF_BUTTON_4): {CONF_EVENT: 18},
    (CONF_DOUBLE_SHORT_RELEASE, CONF_DOUBLE_BUTTON_1): {CONF_EVENT: 101},
    (CONF_DOUBLE_LONG_RELEASE, CONF_DOUBLE_BUTTON_1): {CONF_EVENT: 100},
    (CONF_DOUBLE_SHORT_RELEASE, CONF_DOUBLE_BUTTON_2): {CONF_EVENT: 99},
    (CONF_DOUBLE_LONG_RELEASE, CONF_DOUBLE_BUTTON_2): {CONF_EVENT: 98},
}


REMOTES = {
    HUE_DIMMER_REMOTE_MODEL: HUE_DIMMER_REMOTE,
    HUE_TAP_REMOTE_MODEL: HUE_TAP_REMOTE,
    HUE_BUTTON_REMOTE_MODEL: HUE_BUTTON_REMOTE,
    HUE_FOHSWITCH_REMOTE_MODEL: HUE_FOHSWITCH_REMOTE,
}

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): str, vol.Required(CONF_SUBTYPE): str}
)


def _get_hue_event_from_device_id(opp, device_id):
    """Resolve hue event from device id."""
    for bridge in opp.data.get(DOMAIN, {}).values():
        for hue_event in bridge.sensor_manager.current_events.values():
            if device_id == hue_event.device_registry_id:
                return hue_event

    return None


async def async_validate_trigger_config(opp, config):
    """Validate config."""
    config = TRIGGER_SCHEMA(config)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(config[CONF_DEVICE_ID])

    trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])

    if (
        not device
        or device.model not in REMOTES
        or trigger not in REMOTES[device.model]
    ):
        raise InvalidDeviceAutomationConfig

    return config


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for state changes based on configuration."""
    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(config[CONF_DEVICE_ID])

    hue_event = _get_hue_event_from_device_id(opp, device.id)
    if hue_event is None:
        raise InvalidDeviceAutomationConfig

    trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])

    trigger = REMOTES[device.model][trigger]

    event_config = {
        event_trigger.CONF_PLATFORM: "event",
        event_trigger.CONF_EVENT_TYPE: CONF_HUE_EVENT,
        event_trigger.CONF_EVENT_DATA: {CONF_UNIQUE_ID: hue_event.unique_id, **trigger},
    }

    event_config = event_trigger.TRIGGER_SCHEMA(event_config)
    return await event_trigger.async_attach_trigger(
        opp, event_config, action, automation_info, platform_type="device"
    )


async def async_get_triggers(opp, device_id):
    """List device triggers.

    Make sure device is a supported remote model.
    Retrieve the hue event object matching device entry.
    Generate device trigger list.
    """
    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(device_id)

    if device.model not in REMOTES:
        return

    triggers = []
    for trigger, subtype in REMOTES[device.model]:
        triggers.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_PLATFORM: "device",
                CONF_TYPE: trigger,
                CONF_SUBTYPE: subtype,
            }
        )

    return triggers
