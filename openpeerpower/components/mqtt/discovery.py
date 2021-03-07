"""Support for MQTT discovery."""
import asyncio
from collections import deque
import functools
import json
import logging
import re
import time

from openpeerpower.const import CONF_DEVICE, CONF_PLATFORM
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.loader import async_get_mqtt

from .. import mqtt
from .abbreviations import ABBREVIATIONS, DEVICE_ABBREVIATIONS
from .const import (
    ATTR_DISCOVERY_HASH,
    ATTR_DISCOVERY_PAYLOAD,
    ATTR_DISCOVERY_TOPIC,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

TOPIC_MATCHER = re.compile(
    r"(?P<component>\w+)/(?:(?P<node_id>[a-zA-Z0-9_-]+)/)"
    r"?(?P<object_id>[a-zA-Z0-9_-]+)/config"
)

SUPPORTED_COMPONENTS = [
    "alarm_control_panel",
    "binary_sensor",
    "camera",
    "climate",
    "cover",
    "device_automation",
    "device_tracker",
    "fan",
    "light",
    "lock",
    "number",
    "scene",
    "sensor",
    "switch",
    "tag",
    "vacuum",
]

ALREADY_DISCOVERED = "mqtt_discovered_components"
PENDING_DISCOVERED = "mqtt_pending_components"
CONFIG_ENTRY_IS_SETUP = "mqtt_config_entry_is_setup"
DATA_CONFIG_ENTRY_LOCK = "mqtt_config_entry_lock"
DATA_CONFIG_FLOW_LOCK = "mqtt_discovery_config_flow_lock"
DISCOVERY_UNSUBSCRIBE = "mqtt_discovery_unsubscribe"
INTEGRATION_UNSUBSCRIBE = "mqtt_integration_discovery_unsubscribe"
MQTT_DISCOVERY_UPDATED = "mqtt_discovery_updated_{}"
MQTT_DISCOVERY_NEW = "mqtt_discovery_new_{}_{}"
MQTT_DISCOVERY_DONE = "mqtt_discovery_done_{}"
LAST_DISCOVERY = "mqtt_last_discovery"

TOPIC_BASE = "~"


def clear_discovery_hash(opp, discovery_hash):
    """Clear entry in ALREADY_DISCOVERED list."""
    del opp.data[ALREADY_DISCOVERED][discovery_hash]


def set_discovery_hash(opp, discovery_hash):
    """Clear entry in ALREADY_DISCOVERED list."""
    opp.data[ALREADY_DISCOVERED][discovery_hash] = {}


class MQTTConfig(dict):
    """Dummy class to allow adding attributes."""


async def async_start(
    opp: OpenPeerPowerType, discovery_topic, config_entry=None
) -> bool:
    """Start MQTT Discovery."""
    mqtt_integrations = {}

    async def async_discovery_message_received(msg):
        """Process the received message."""
        opp.data[LAST_DISCOVERY] = time.time()
        payload = msg.payload
        topic = msg.topic
        topic_trimmed = topic.replace(f"{discovery_topic}/", "", 1)
        match = TOPIC_MATCHER.match(topic_trimmed)

        if not match:
            return

        component, node_id, object_id = match.groups()

        if component not in SUPPORTED_COMPONENTS:
            _LOGGER.warning("Integration %s is not supported", component)
            return

        if payload:
            try:
                payload = json.loads(payload)
            except ValueError:
                _LOGGER.warning("Unable to parse JSON %s: '%s'", object_id, payload)
                return

        payload = MQTTConfig(payload)

        for key in list(payload):
            abbreviated_key = key
            key = ABBREVIATIONS.get(key, key)
            payload[key] = payload.pop(abbreviated_key)

        if CONF_DEVICE in payload:
            device = payload[CONF_DEVICE]
            for key in list(device):
                abbreviated_key = key
                key = DEVICE_ABBREVIATIONS.get(key, key)
                device[key] = device.pop(abbreviated_key)

        if TOPIC_BASE in payload:
            base = payload.pop(TOPIC_BASE)
            for key, value in payload.items():
                if isinstance(value, str) and value:
                    if value[0] == TOPIC_BASE and key.endswith("topic"):
                        payload[key] = f"{base}{value[1:]}"
                    if value[-1] == TOPIC_BASE and key.endswith("topic"):
                        payload[key] = f"{value[:-1]}{base}"

        # If present, the node_id will be included in the discovered object id
        discovery_id = " ".join((node_id, object_id)) if node_id else object_id
        discovery_hash = (component, discovery_id)

        if payload:
            # Attach MQTT topic to the payload, used for debug prints
            setattr(payload, "__configuration_source__", f"MQTT (topic: '{topic}')")
            discovery_data = {
                ATTR_DISCOVERY_HASH: discovery_hash,
                ATTR_DISCOVERY_PAYLOAD: payload,
                ATTR_DISCOVERY_TOPIC: topic,
            }
            setattr(payload, "discovery_data", discovery_data)

            payload[CONF_PLATFORM] = "mqtt"

        if discovery_hash in opp.data[PENDING_DISCOVERED]:
            pending = opp.data[PENDING_DISCOVERED][discovery_hash]["pending"]
            pending.appendleft(payload)
            _LOGGER.info(
                "Component has already been discovered: %s %s, queuing update",
                component,
                discovery_id,
            )
            return

        await async_process_discovery_payload(component, discovery_id, payload)

    async def async_process_discovery_payload(component, discovery_id, payload):

        _LOGGER.debug("Process discovery payload %s", payload)
        discovery_hash = (component, discovery_id)
        if discovery_hash in opp.data[ALREADY_DISCOVERED] or payload:

            async def discovery_done(_):
                pending = opp.data[PENDING_DISCOVERED][discovery_hash]["pending"]
                _LOGGER.debug("Pending discovery for %s: %s", discovery_hash, pending)
                if not pending:
                    opp.data[PENDING_DISCOVERED][discovery_hash]["unsub"]()
                    opp.data[PENDING_DISCOVERED].pop(discovery_hash)
                else:
                    payload = pending.pop()
                    await async_process_discovery_payload(
                        component, discovery_id, payload
                    )

            if discovery_hash not in opp.data[PENDING_DISCOVERED]:
                opp.data[PENDING_DISCOVERED][discovery_hash] = {
                    "unsub": async_dispatcher_connect(
                        opp,
                        MQTT_DISCOVERY_DONE.format(discovery_hash),
                        discovery_done,
                    ),
                    "pending": deque([]),
                }

        if discovery_hash in opp.data[ALREADY_DISCOVERED]:
            # Dispatch update
            _LOGGER.info(
                "Component has already been discovered: %s %s, sending update",
                component,
                discovery_id,
            )
            async_dispatcher_send(
                opp, MQTT_DISCOVERY_UPDATED.format(discovery_hash), payload
            )
        elif payload:
            # Add component
            _LOGGER.info("Found new component: %s %s", component, discovery_id)
            opp.data[ALREADY_DISCOVERED][discovery_hash] = None

            config_entries_key = f"{component}.mqtt"
            async with opp.data[DATA_CONFIG_ENTRY_LOCK]:
                if config_entries_key not in opp.data[CONFIG_ENTRY_IS_SETUP]:
                    if component == "device_automation":
                        # Local import to avoid circular dependencies
                        # pylint: disable=import-outside-toplevel
                        from . import device_automation

                        await device_automation.async_setup_entry(opp, config_entry)
                    elif component == "tag":
                        # Local import to avoid circular dependencies
                        # pylint: disable=import-outside-toplevel
                        from . import tag

                        await tag.async_setup_entry(opp, config_entry)
                    else:
                        await opp.config_entries.async_forward_entry_setup(
                            config_entry, component
                        )
                    opp.data[CONFIG_ENTRY_IS_SETUP].add(config_entries_key)

            async_dispatcher_send(
                opp, MQTT_DISCOVERY_NEW.format(component, "mqtt"), payload
            )
        else:
            # Unhandled discovery message
            async_dispatcher_send(opp, MQTT_DISCOVERY_DONE.format(discovery_hash), None)

    opp.data[DATA_CONFIG_ENTRY_LOCK] = asyncio.Lock()
    opp.data[DATA_CONFIG_FLOW_LOCK] = asyncio.Lock()
    opp.data[CONFIG_ENTRY_IS_SETUP] = set()

    opp.data[ALREADY_DISCOVERED] = {}
    opp.data[PENDING_DISCOVERED] = {}

    discovery_topics = [
        f"{discovery_topic}/+/+/config",
        f"{discovery_topic}/+/+/+/config",
    ]
    opp.data[DISCOVERY_UNSUBSCRIBE] = await asyncio.gather(
        *(
            mqtt.async_subscribe(opp, topic, async_discovery_message_received, 0)
            for topic in discovery_topics
        )
    )

    opp.data[LAST_DISCOVERY] = time.time()
    mqtt_integrations = await async_get_mqtt(opp)

    opp.data[INTEGRATION_UNSUBSCRIBE] = {}

    for (integration, topics) in mqtt_integrations.items():

        async def async_integration_message_received(integration, msg):
            """Process the received message."""
            key = f"{integration}_{msg.subscribed_topic}"

            # Lock to prevent initiating many parallel config flows.
            # Note: The lock is not intended to prevent a race, only for performance
            async with opp.data[DATA_CONFIG_FLOW_LOCK]:
                # Already unsubscribed
                if key not in opp.data[INTEGRATION_UNSUBSCRIBE]:
                    return

                result = await opp.config_entries.flow.async_init(
                    integration, context={"source": DOMAIN}, data=msg
                )
                if (
                    result
                    and result["type"] == "abort"
                    and result["reason"]
                    in ["already_configured", "single_instance_allowed"]
                ):
                    unsub = opp.data[INTEGRATION_UNSUBSCRIBE].pop(key, None)
                    if unsub is None:
                        return
                    unsub()

        for topic in topics:
            key = f"{integration}_{topic}"
            opp.data[INTEGRATION_UNSUBSCRIBE][key] = await mqtt.async_subscribe(
                opp,
                topic,
                functools.partial(async_integration_message_received, integration),
                0,
            )

    return True


async def async_stop(opp: OpenPeerPowerType) -> bool:
    """Stop MQTT Discovery."""
    if DISCOVERY_UNSUBSCRIBE in opp.data:
        for unsub in opp.data[DISCOVERY_UNSUBSCRIBE]:
            unsub()
        opp.data[DISCOVERY_UNSUBSCRIBE] = []
    if INTEGRATION_UNSUBSCRIBE in opp.data:
        for key, unsub in list(opp.data[INTEGRATION_UNSUBSCRIBE].items()):
            unsub()
            opp.data[INTEGRATION_UNSUBSCRIBE].pop(key)
