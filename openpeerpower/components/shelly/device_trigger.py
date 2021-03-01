"""Provides device triggers for Shelly."""
from typing import List

import voluptuous as vol

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from openpeerpower.components.openpeerpower.triggers import event as event_trigger
from openpeerpower.const import (
    ATTR_DEVICE_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
)
from openpeerpower.core import CALLBACK_TYPE, OpenPeerPower
from openpeerpower.helpers.typing import ConfigType

from .const import (
    ATTR_CHANNEL,
    ATTR_CLICK_TYPE,
    CONF_SUBTYPE,
    DOMAIN,
    EVENT_SHELLY_CLICK,
    INPUTS_EVENTS_SUBTYPES,
    SUPPORTED_INPUTS_EVENTS_TYPES,
)
from .utils import get_device_wrapper, get_input_triggers

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(SUPPORTED_INPUTS_EVENTS_TYPES),
        vol.Required(CONF_SUBTYPE): vol.In(INPUTS_EVENTS_SUBTYPES),
    }
)


async def async_validate_trigger_config(opp, config):
    """Validate config."""
    config = TRIGGER_SCHEMA(config)

    # if device is available verify parameters against device capabilities
    wrapper = get_device_wrapper(opp, config[CONF_DEVICE_ID])
    if not wrapper:
        return config

    trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])

    for block in wrapper.device.blocks:
        input_triggers = get_input_triggers(wrapper.device, block)
        if trigger in input_triggers:
            return config

    raise InvalidDeviceAutomationConfig(
        f"Invalid ({CONF_TYPE},{CONF_SUBTYPE}): {trigger}"
    )


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device triggers for Shelly devices."""
    triggers = []

    wrapper = get_device_wrapper(opp, device_id)
    if not wrapper:
        raise InvalidDeviceAutomationConfig(f"Device not found: {device_id}")

    for block in wrapper.device.blocks:
        input_triggers = get_input_triggers(wrapper.device, block)

        for trigger, subtype in input_triggers:
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_TYPE: trigger,
                    CONF_SUBTYPE: subtype,
                }
            )

    return triggers


async def async_attach_trigger(
    opp: OpenPeerPower,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    config = TRIGGER_SCHEMA(config)
    event_config = {
        event_trigger.CONF_PLATFORM: CONF_EVENT,
        event_trigger.CONF_EVENT_TYPE: EVENT_SHELLY_CLICK,
        event_trigger.CONF_EVENT_DATA: {
            ATTR_DEVICE_ID: config[CONF_DEVICE_ID],
            ATTR_CHANNEL: INPUTS_EVENTS_SUBTYPES[config[CONF_SUBTYPE]],
            ATTR_CLICK_TYPE: config[CONF_TYPE],
        },
    }
    event_config = event_trigger.TRIGGER_SCHEMA(event_config)
    return await event_trigger.async_attach_trigger(
        opp, event_config, action, automation_info, platform_type="device"
    )
