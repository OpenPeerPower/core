"""Provides device automations for Netatmo."""
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
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
)
from openpeerpower.core import CALLBACK_TYPE, OpenPeerPower
from openpeerpower.helpers import config_validation as cv, entity_registry
from openpeerpower.helpers.typing import ConfigType

from . import DOMAIN
from .climate import STATE_NETATMO_AWAY, STATE_NETATMO_HG, STATE_NETATMO_SCHEDULE
from .const import (
    CLIMATE_TRIGGERS,
    EVENT_TYPE_THERM_MODE,
    INDOOR_CAMERA_TRIGGERS,
    MODEL_NACAMERA,
    MODEL_NATHERM1,
    MODEL_NOC,
    MODEL_NRV,
    NETATMO_EVENT,
    OUTDOOR_CAMERA_TRIGGERS,
)

CONF_SUBTYPE = "subtype"

DEVICES = {
    MODEL_NACAMERA: INDOOR_CAMERA_TRIGGERS,
    MODEL_NOC: OUTDOOR_CAMERA_TRIGGERS,
    MODEL_NATHERM1: CLIMATE_TRIGGERS,
    MODEL_NRV: CLIMATE_TRIGGERS,
}

SUBTYPES = {
    EVENT_TYPE_THERM_MODE: [
        STATE_NETATMO_SCHEDULE,
        STATE_NETATMO_HG,
        STATE_NETATMO_AWAY,
    ]
}

TRIGGER_TYPES = OUTDOOR_CAMERA_TRIGGERS + INDOOR_CAMERA_TRIGGERS + CLIMATE_TRIGGERS

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Optional(CONF_SUBTYPE): str,
    }
)


async def async_validate_trigger_config(opp, config):
    """Validate config."""
    config = TRIGGER_SCHEMA(config)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(config[CONF_DEVICE_ID])

    trigger = config[CONF_TYPE]

    if (
        not device
        or device.model not in DEVICES
        or trigger not in DEVICES[device.model]
    ):
        raise InvalidDeviceAutomationConfig(f"Unsupported model {device.model}")

    return config


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device triggers for Netatmo devices."""
    registry = await entity_registry.async_get_registry(opp)
    device_registry = await opp.helpers.device_registry.async_get_registry()
    triggers = []

    for entry in entity_registry.async_entries_for_device(registry, device_id):
        device = device_registry.async_get(device_id)

        for trigger in DEVICES.get(device.model, []):
            if trigger in SUBTYPES:
                for subtype in SUBTYPES[trigger]:
                    triggers.append(
                        {
                            CONF_PLATFORM: "device",
                            CONF_DEVICE_ID: device_id,
                            CONF_DOMAIN: DOMAIN,
                            CONF_ENTITY_ID: entry.entity_id,
                            CONF_TYPE: trigger,
                            CONF_SUBTYPE: subtype,
                        }
                    )
            else:
                triggers.append(
                    {
                        CONF_PLATFORM: "device",
                        CONF_DEVICE_ID: device_id,
                        CONF_DOMAIN: DOMAIN,
                        CONF_ENTITY_ID: entry.entity_id,
                        CONF_TYPE: trigger,
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

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get(config[CONF_DEVICE_ID])

    if not device:
        return

    if device.model not in DEVICES:
        return

    event_config = {
        event_trigger.CONF_PLATFORM: "event",
        event_trigger.CONF_EVENT_TYPE: NETATMO_EVENT,
        event_trigger.CONF_EVENT_DATA: {
            "type": config[CONF_TYPE],
            ATTR_DEVICE_ID: config[ATTR_DEVICE_ID],
        },
    }
    if config[CONF_TYPE] in SUBTYPES:
        event_config[event_trigger.CONF_EVENT_DATA]["data"] = {
            "mode": config[CONF_SUBTYPE]
        }

    event_config = event_trigger.TRIGGER_SCHEMA(event_config)
    return await event_trigger.async_attach_trigger(
        opp, event_config, action, automation_info, platform_type="device"
    )
