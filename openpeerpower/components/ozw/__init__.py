"""The ozw integration."""
import asyncio
import json
import logging

from openzwavemqtt import OZWManager, OZWOptions
from openzwavemqtt.const import (
    EVENT_INSTANCE_EVENT,
    EVENT_NODE_ADDED,
    EVENT_NODE_CHANGED,
    EVENT_NODE_REMOVED,
    EVENT_VALUE_ADDED,
    EVENT_VALUE_CHANGED,
    EVENT_VALUE_REMOVED,
    CommandClass,
    ValueType,
)
from openzwavemqtt.models.node import OZWNode
from openzwavemqtt.models.value import OZWValue
from openzwavemqtt.util.mqtt_client import MQTTClient

from openpeerpower.components import mqtt
from openpeerpower.components.oppio.handler import OppioAPIError
from openpeerpower.config_entries import ENTRY_STATE_LOADED, ConfigEntry
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.device_registry import async_get_registry as get_dev_reg
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from . import const
from .const import (
    CONF_INTEGRATION_CREATED_ADDON,
    CONF_USE_ADDON,
    DATA_UNSUBSCRIBE,
    DOMAIN,
    MANAGER,
    NODES_VALUES,
    PLATFORMS,
    TOPIC_OPENZWAVE,
)
from .discovery import DISCOVERY_SCHEMAS, check_node_schema, check_value_schema
from .entity import (
    ZWaveDeviceEntityValues,
    create_device_id,
    create_device_name,
    create_value_id,
)
from .services import ZWaveServices
from .websocket_api import async_register_api

_LOGGER = logging.getLogger(__name__)

DATA_DEVICES = "zwave-mqtt-devices"
DATA_STOP_MQTT_CLIENT = "ozw_stop_mqtt_client"


async def async_setup(opp: OpenPeerPower, config: dict):
    """Initialize basic config of ozw component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up ozw from a config entry."""
    ozw_data = opp.data[DOMAIN][entry.entry_id] = {}
    ozw_data[DATA_UNSUBSCRIBE] = []

    data_nodes = {}
    opp.data[DOMAIN][NODES_VALUES] = data_values = {}
    removed_nodes = []
    manager_options = {"topic_prefix": f"{TOPIC_OPENZWAVE}/"}

    if entry.unique_id is None:
        opp.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    if entry.data.get(CONF_USE_ADDON):
        # Do not use MQTT integration. Use own MQTT client.
        # Retrieve discovery info from the OpenZWave add-on.
        discovery_info = await opp.components.oppio.async_get_addon_discovery_info(
            "core_zwave"
        )

        if not discovery_info:
            _LOGGER.error("Failed to get add-on discovery info")
            raise ConfigEntryNotReady

        discovery_info_config = discovery_info["config"]

        host = discovery_info_config["host"]
        port = discovery_info_config["port"]
        username = discovery_info_config["username"]
        password = discovery_info_config["password"]
        mqtt_client = MQTTClient(host, port, username=username, password=password)
        manager_options["send_message"] = mqtt_client.send_message

    else:
        mqtt_entries = opp.config_entries.async_entries("mqtt")
        if not mqtt_entries or mqtt_entries[0].state != ENTRY_STATE_LOADED:
            _LOGGER.error("MQTT integration is not set up")
            return False

        mqtt_entry = mqtt_entries[0]  # MQTT integration only has one entry.

        @callback
        def send_message(topic, payload):
            if mqtt_entry.state != ENTRY_STATE_LOADED:
                _LOGGER.error("MQTT integration is not set up")
                return

            mqtt.async_publish(opp, topic, json.dumps(payload))

        manager_options["send_message"] = send_message

    options = OZWOptions(**manager_options)
    manager = OZWManager(options)

    opp.data[DOMAIN][MANAGER] = manager

    @callback
    def async_node_added(node):
        # Caution: This is also called on (re)start.
        _LOGGER.debug("[NODE ADDED] node_id: %s", node.id)
        data_nodes[node.id] = node
        if node.id not in data_values:
            data_values[node.id] = []

    @callback
    def async_node_changed(node):
        _LOGGER.debug("[NODE CHANGED] node_id: %s", node.id)
        data_nodes[node.id] = node
        # notify devices about the node change
        if node.id not in removed_nodes:
            opp.async_create_task(async_handle_node_update(opp, node))

    @callback
    def async_node_removed(node):
        _LOGGER.debug("[NODE REMOVED] node_id: %s", node.id)
        data_nodes.pop(node.id)
        # node added/removed events also happen on (re)starts of opp/mqtt/ozw
        # cleanup device/entity registry if we know this node is permanently deleted
        # entities itself are removed by the values logic
        if node.id in removed_nodes:
            opp.async_create_task(async_handle_remove_node(opp, node))
            removed_nodes.remove(node.id)

    @callback
    def async_instance_event(message):
        event = message["event"]
        event_data = message["data"]
        _LOGGER.debug("[INSTANCE EVENT]: %s - data: %s", event, event_data)
        # The actual removal action of a Z-Wave node is reported as instance event
        # Only when this event is detected we cleanup the device and entities from opp
        # Note: Find a more elegant way of doing this, e.g. a notification of this event from OZW
        if event in ["removenode", "removefailednode"] and "Node" in event_data:
            removed_nodes.append(event_data["Node"])

    @callback
    def async_value_added(value):
        node = value.node
        # Clean up node.node_id and node.id use. They are the same.
        node_id = value.node.node_id

        # Filter out CommandClasses we're definitely not interested in.
        if value.command_class in [
            CommandClass.MANUFACTURER_SPECIFIC,
        ]:
            return

        _LOGGER.debug(
            "[VALUE ADDED] node_id: %s - label: %s - value: %s - value_id: %s - CC: %s",
            value.node.id,
            value.label,
            value.value,
            value.value_id_key,
            value.command_class,
        )

        node_data_values = data_values[node_id]

        # Check if this value should be tracked by an existing entity
        value_unique_id = create_value_id(value)
        for values in node_data_values:
            values.async_check_value(value)
            if values.values_id == value_unique_id:
                return  # this value already has an entity

        # Run discovery on it and see if any entities need created
        for schema in DISCOVERY_SCHEMAS:
            if not check_node_schema(node, schema):
                continue
            if not check_value_schema(
                value, schema[const.DISC_VALUES][const.DISC_PRIMARY]
            ):
                continue

            values = ZWaveDeviceEntityValues(opp, options, schema, value)
            values.async_setup()

            # This is legacy and can be cleaned up since we are in the main thread:
            # We create a new list and update the reference here so that
            # the list can be safely iterated over in the main thread
            data_values[node_id] = node_data_values + [values]

    @callback
    def async_value_changed(value):
        # if an entity belonging to this value needs updating,
        # it's handled within the entity logic
        _LOGGER.debug(
            "[VALUE CHANGED] node_id: %s - label: %s - value: %s - value_id: %s - CC: %s",
            value.node.id,
            value.label,
            value.value,
            value.value_id_key,
            value.command_class,
        )
        # Handle a scene activation message
        if value.command_class in [
            CommandClass.SCENE_ACTIVATION,
            CommandClass.CENTRAL_SCENE,
        ]:
            async_handle_scene_activated(opp, value)
            return

    @callback
    def async_value_removed(value):
        _LOGGER.debug(
            "[VALUE REMOVED] node_id: %s - label: %s - value: %s - value_id: %s - CC: %s",
            value.node.id,
            value.label,
            value.value,
            value.value_id_key,
            value.command_class,
        )
        # signal all entities using this value for removal
        value_unique_id = create_value_id(value)
        async_dispatcher_send(opp, const.SIGNAL_DELETE_ENTITY, value_unique_id)
        # remove value from our local list
        node_data_values = data_values[value.node.id]
        node_data_values[:] = [
            item for item in node_data_values if item.values_id != value_unique_id
        ]

    # Listen to events for node and value changes
    for event, event_callback in (
        (EVENT_NODE_ADDED, async_node_added),
        (EVENT_NODE_CHANGED, async_node_changed),
        (EVENT_NODE_REMOVED, async_node_removed),
        (EVENT_VALUE_ADDED, async_value_added),
        (EVENT_VALUE_CHANGED, async_value_changed),
        (EVENT_VALUE_REMOVED, async_value_removed),
        (EVENT_INSTANCE_EVENT, async_instance_event),
    ):
        ozw_data[DATA_UNSUBSCRIBE].append(options.listen(event, event_callback))

    # Register Services
    services = ZWaveServices(opp, manager)
    services.async_register()

    # Register WebSocket API
    async_register_api(opp)

    @callback
    def async_receive_message(msg):
        manager.receive_message(msg.topic, msg.payload)

    async def start_platforms():
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_setup(entry, platform)
                for platform in PLATFORMS
            ]
        )
        if entry.data.get(CONF_USE_ADDON):
            mqtt_client_task = asyncio.create_task(mqtt_client.start_client(manager))

            async def async_stop_mqtt_client(event=None):
                """Stop the mqtt client.

                Do not unsubscribe the manager topic.
                """
                mqtt_client_task.cancel()
                try:
                    await mqtt_client_task
                except asyncio.CancelledError:
                    pass

            ozw_data[DATA_UNSUBSCRIBE].append(
                opp.bus.async_listen_once(
                    EVENT_OPENPEERPOWER_STOP, async_stop_mqtt_client
                )
            )
            ozw_data[DATA_STOP_MQTT_CLIENT] = async_stop_mqtt_client

        else:
            ozw_data[DATA_UNSUBSCRIBE].append(
                await mqtt.async_subscribe(
                    opp, f"{manager.options.topic_prefix}#", async_receive_message
                )
            )

    opp.async_create_task(start_platforms())

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    # cleanup platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    # unsubscribe all listeners
    for unsubscribe_listener in opp.data[DOMAIN][entry.entry_id][DATA_UNSUBSCRIBE]:
        unsubscribe_listener()

    if entry.data.get(CONF_USE_ADDON):
        async_stop_mqtt_client = opp.data[DOMAIN][entry.entry_id][DATA_STOP_MQTT_CLIENT]
        await async_stop_mqtt_client()

    opp.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_remove_entry(opp: OpenPeerPower, entry: ConfigEntry) -> None:
    """Remove a config entry."""
    if not entry.data.get(CONF_INTEGRATION_CREATED_ADDON):
        return

    try:
        await opp.components.oppio.async_stop_addon("core_zwave")
    except OppioAPIError as err:
        _LOGGER.error("Failed to stop the OpenZWave add-on: %s", err)
        return
    try:
        await opp.components.oppio.async_uninstall_addon("core_zwave")
    except OppioAPIError as err:
        _LOGGER.error("Failed to uninstall the OpenZWave add-on: %s", err)


async def async_handle_remove_node(opp: OpenPeerPower, node: OZWNode):
    """Handle the removal of a Z-Wave node, removing all traces in device/entity registry."""
    dev_registry = await get_dev_reg(opp)
    # grab device in device registry attached to this node
    dev_id = create_device_id(node)
    device = dev_registry.async_get_device({(DOMAIN, dev_id)})
    if not device:
        return
    devices_to_remove = [device.id]
    # also grab slave devices (node instances)
    for item in dev_registry.devices.values():
        if item.via_device_id == device.id:
            devices_to_remove.append(item.id)
    # remove all devices in registry related to this node
    # note: removal of entity registry is handled by core
    for dev_id in devices_to_remove:
        dev_registry.async_remove_device(dev_id)


async def async_handle_node_update(opp: OpenPeerPower, node: OZWNode):
    """
    Handle a node updated event from OZW.

    Meaning some of the basic info like name/model is updated.
    We want these changes to be pushed to the device registry.
    """
    dev_registry = await get_dev_reg(opp)
    # grab device in device registry attached to this node
    dev_id = create_device_id(node)
    device = dev_registry.async_get_device({(DOMAIN, dev_id)})
    if not device:
        return
    # update device in device registry with (updated) info
    for item in dev_registry.devices.values():
        if item.id != device.id and item.via_device_id != device.id:
            continue
        dev_name = create_device_name(node)
        dev_registry.async_update_device(
            item.id,
            manufacturer=node.node_manufacturer_name,
            model=node.node_product_name,
            name=dev_name,
        )


@callback
def async_handle_scene_activated(opp: OpenPeerPower, scene_value: OZWValue):
    """Handle a (central) scene activation message."""
    node_id = scene_value.node.id
    ozw_instance_id = scene_value.ozw_instance.id
    scene_id = scene_value.index
    scene_label = scene_value.label
    if scene_value.command_class == CommandClass.SCENE_ACTIVATION:
        # legacy/network scene
        scene_value_id = scene_value.value
        scene_value_label = scene_value.label
    else:
        # central scene command
        if scene_value.type != ValueType.LIST:
            return
        scene_value_label = scene_value.value["Selected"]
        scene_value_id = scene_value.value["Selected_id"]

    _LOGGER.debug(
        "[SCENE_ACTIVATED] ozw_instance: %s - node_id: %s - scene_id: %s - scene_value_id: %s",
        ozw_instance_id,
        node_id,
        scene_id,
        scene_value_id,
    )
    # Simply forward it to the opp event bus
    opp.bus.async_fire(
        const.EVENT_SCENE_ACTIVATED,
        {
            const.ATTR_INSTANCE_ID: ozw_instance_id,
            const.ATTR_NODE_ID: node_id,
            const.ATTR_SCENE_ID: scene_id,
            const.ATTR_SCENE_LABEL: scene_label,
            const.ATTR_SCENE_VALUE_ID: scene_value_id,
            const.ATTR_SCENE_VALUE_LABEL: scene_value_label,
        },
    )
