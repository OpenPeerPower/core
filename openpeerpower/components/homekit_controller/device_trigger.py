"""Provides device automations for homekit devices."""
from typing import List

from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.characteristics.const import InputEventValues
from aiohomekit.model.services import ServicesTypes
from aiohomekit.utils import clamp_enum_to_char
import voluptuous as vol

from openpeerpower.components.automation import AutomationActionType
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from openpeerpower.core import CALLBACK_TYPE, OpenPeerPower, callback
from openpeerpower.helpers.typing import ConfigType

from .const import DOMAIN, KNOWN_DEVICES, TRIGGERS

TRIGGER_TYPES = {
    "button1",
    "button2",
    "button3",
    "button4",
    "button5",
    "button6",
    "button7",
    "button8",
    "button9",
    "button10",
}
TRIGGER_SUBTYPES = {"single_press", "double_press", "long_press"}

CONF_IID = "iid"
CONF_SUBTYPE = "subtype"

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Required(CONF_SUBTYPE): vol.In(TRIGGER_SUBTYPES),
    }
)

HK_TO_HA_INPUT_EVENT_VALUES = {
    InputEventValues.SINGLE_PRESS: "single_press",
    InputEventValues.DOUBLE_PRESS: "double_press",
    InputEventValues.LONG_PRESS: "long_press",
}


class TriggerSource:
    """Represents a stateless source of event data from HomeKit."""

    def __init__(self, connection, aid, triggers):
        """Initialize a set of triggers for a device."""
        self._opp = connection.opp
        self._connection = connection
        self._aid = aid
        self._triggers = {}
        for trigger in triggers:
            self._triggers[(trigger["type"], trigger["subtype"])] = trigger
        self._callbacks = {}

    def fire(self, iid, value):
        """Process events that have been received from a HomeKit accessory."""
        for event_handler in self._callbacks.get(iid, []):
            event_handler(value)

    def async_get_triggers(self):
        """List device triggers for homekit devices."""
        yield from self._triggers

    async def async_attach_trigger(
        self,
        config: TRIGGER_SCHEMA,
        action: AutomationActionType,
        automation_info: dict,
    ) -> CALLBACK_TYPE:
        """Attach a trigger."""

        def event_handler(char):
            if config[CONF_SUBTYPE] != HK_TO_HA_INPUT_EVENT_VALUES[char["value"]]:
                return
            self._opp.async_create_task(action({"trigger": config}))

        trigger = self._triggers[config[CONF_TYPE], config[CONF_SUBTYPE]]
        iid = trigger["characteristic"]

        self._connection.add_watchable_characteristics([(self._aid, iid)])
        self._callbacks.setdefault(iid, []).append(event_handler)

        def async_remove_handler():
            if iid in self._callbacks:
                self._callbacks[iid].remove(event_handler)

        return async_remove_handler


def enumerate_stateless_switch(service):
    """Enumerate a stateless switch, like a single button."""

    # A stateless switch that has a SERVICE_LABEL_INDEX is part of a group
    # And is handled separately
    if service.has(CharacteristicsTypes.SERVICE_LABEL_INDEX):
        if len(service.linked) > 0:
            return []

    char = service[CharacteristicsTypes.INPUT_EVENT]

    # HomeKit itself supports single, double and long presses. But the
    # manufacturer might not - clamp options to what they say.
    all_values = clamp_enum_to_char(InputEventValues, char)

    results = []
    for event_type in all_values:
        results.append(
            {
                "characteristic": char.iid,
                "value": event_type,
                "type": "button1",
                "subtype": HK_TO_HA_INPUT_EVENT_VALUES[event_type],
            }
        )
    return results


def enumerate_stateless_switch_group(service):
    """Enumerate a group of stateless switches, like a remote control."""
    switches = list(
        service.accessory.services.filter(
            service_type=ServicesTypes.STATELESS_PROGRAMMABLE_SWITCH,
            child_service=service,
            order_by=[CharacteristicsTypes.SERVICE_LABEL_INDEX],
        )
    )

    results = []
    for idx, switch in enumerate(switches):
        char = switch[CharacteristicsTypes.INPUT_EVENT]

        # HomeKit itself supports single, double and long presses. But the
        # manufacturer might not - clamp options to what they say.
        all_values = clamp_enum_to_char(InputEventValues, char)

        for event_type in all_values:
            results.append(
                {
                    "characteristic": char.iid,
                    "value": event_type,
                    "type": f"button{idx + 1}",
                    "subtype": HK_TO_HA_INPUT_EVENT_VALUES[event_type],
                }
            )
    return results


def enumerate_doorbell(service):
    """Enumerate doorbell buttons."""
    input_event = service[CharacteristicsTypes.INPUT_EVENT]

    # HomeKit itself supports single, double and long presses. But the
    # manufacturer might not - clamp options to what they say.
    all_values = clamp_enum_to_char(InputEventValues, input_event)

    results = []
    for event_type in all_values:
        results.append(
            {
                "characteristic": input_event.iid,
                "value": event_type,
                "type": "doorbell",
                "subtype": HK_TO_HA_INPUT_EVENT_VALUES[event_type],
            }
        )
    return results


TRIGGER_FINDERS = {
    ServicesTypes.SERVICE_LABEL: enumerate_stateless_switch_group,
    ServicesTypes.STATELESS_PROGRAMMABLE_SWITCH: enumerate_stateless_switch,
    ServicesTypes.DOORBELL: enumerate_doorbell,
}


async def async_setup_triggers_for_entry(opp: OpenPeerPower, config_entry):
    """Triggers aren't entities as they have no state, but we still need to set them up for a config entry."""
    hkid = config_entry.data["AccessoryPairingID"]
    conn = opp.data[KNOWN_DEVICES][hkid]

    @callback
    def async_add_service(service):
        aid = service.accessory.aid
        service_type = service.short_type

        # If not a known service type then we can't handle any stateless events for it
        if service_type not in TRIGGER_FINDERS:
            return False

        # We can't have multiple trigger sources for the same device id
        # Can't have a doorbell and a remote control in the same accessory
        # They have to be different accessories (they can be on the same bridge)
        # In practice, this is inline with what iOS actually supports AFAWCT.
        device_id = conn.devices[aid]
        if device_id in opp.data[TRIGGERS]:
            return False

        # Just because we recognise the service type doesn't mean we can actually
        # extract any triggers - so only proceed if we can
        triggers = TRIGGER_FINDERS[service_type](service)
        if len(triggers) == 0:
            return False

        trigger = TriggerSource(conn, aid, triggers)
        opp.data[TRIGGERS][device_id] = trigger

        return True

    conn.add_listener(async_add_service)


def async_fire_triggers(conn, events):
    """Process events generated by a HomeKit accessory into automation triggers."""
    for (aid, iid), ev in events.items():
        if aid in conn.devices:
            device_id = conn.devices[aid]
            if device_id in conn.opp.data[TRIGGERS]:
                source = conn.opp.data[TRIGGERS][device_id]
                source.fire(iid, ev)


async def async_get_triggers(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device triggers for homekit devices."""

    if device_id not in opp.data.get(TRIGGERS, {}):
        return []

    device = opp.data[TRIGGERS][device_id]

    triggers = []

    for trigger, subtype in device.async_get_triggers():
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

    device_id = config[CONF_DEVICE_ID]
    device = opp.data[TRIGGERS][device_id]
    return await device.async_attach_trigger(config, action, automation_info)
