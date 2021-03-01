"""Provides device automations for Nest."""
from typing import List

import voluptuous as vol

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from openpeerpower.components.openpeerpower.triggers import event as event_trigger
from openpeerpower.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from openpeerpower.core import CALLBACK_TYPE, OpenPeerPower
from openpeerpower.helpers.typing import ConfigType

from .const import DATA_SUBSCRIBER, DOMAIN
from .events import DEVICE_TRAIT_TRIGGER_MAP, NEST_EVENT

DEVICE = "device"

TRIGGER_TYPES = set(DEVICE_TRAIT_TRIGGER_MAP.values())

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_nest_device_id(opp: OpenPeerPower, device_id: str) -> str:
    """Get the nest API device_id from the OpenPeerPower device_id."""
    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(device_id)
    for (domain, unique_id) in device.identifiers:
        if domain == DOMAIN:
            return unique_id
    return None


async def async_get_device_trigger_types(
    opp: OpenPeerPower, nest_device_id: str
) -> List[str]:
    """List event triggers supported for a Nest device."""
    # All devices should have already been loaded so any failures here are
    # "shouldn't happen" cases
    subscriber = opp.data[DOMAIN][DATA_SUBSCRIBER]
    device_manager = await subscriber.async_get_device_manager()
    nest_device = device_manager.devices.get(nest_device_id)
    if not nest_device:
        raise InvalidDeviceAutomationConfig(f"Nest device not found {nest_device_id}")

    # Determine the set of event types based on the supported device traits
    trigger_types = []
    for trait in nest_device.traits:
        trigger_type = DEVICE_TRAIT_TRIGGER_MAP.get(trait)
        if trigger_type:
            trigger_types.append(trigger_type)
    return trigger_types


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device triggers for a Nest device."""
    nest_device_id = await async_get_nest_device_id(opp, device_id)
    if not nest_device_id:
        raise InvalidDeviceAutomationConfig(f"Device not found {device_id}")
    trigger_types = await async_get_device_trigger_types(opp, nest_device_id)
    return [
        {
            CONF_PLATFORM: DEVICE,
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: trigger_type,
        }
        for trigger_type in trigger_types
    ]


async def async_attach_trigger(
    opp: OpenPeerPower,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    config = TRIGGER_SCHEMA(config)
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: NEST_EVENT,
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_TYPE: config[CONF_TYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        opp, event_config, action, automation_info, platform_type="device"
    )
