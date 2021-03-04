"""Websocket API for Z-Wave JS."""
import dataclasses
import json
from typing import Dict

from aiohttp import hdrs, web, web_exceptions
import voluptuous as vol
from zwave_js_server import dump
from zwave_js_server.const import LogLevel
from zwave_js_server.exceptions import InvalidNewValue, NotFoundError, SetValueFailed
from zwave_js_server.model.log_config import LogConfig
from zwave_js_server.util.node import async_set_config_parameter

from openpeerpower.components import websocket_api
from openpeerpower.components.http.view import OpenPeerPowerView
from openpeerpower.components.websocket_api.connection import ActiveConnection
from openpeerpower.components.websocket_api.const import (
    ERR_NOT_FOUND,
    ERR_NOT_SUPPORTED,
    ERR_UNKNOWN_ERROR,
)
from openpeerpower.const import CONF_URL
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.device_registry import DeviceEntry
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import DATA_CLIENT, DOMAIN, EVENT_DEVICE_ADDED_TO_REGISTRY

# general API constants
ID = "id"
ENTRY_ID = "entry_id"
NODE_ID = "node_id"
TYPE = "type"
PROPERTY = "property"
PROPERTY_KEY = "property_key"
VALUE = "value"

# constants for log config commands
CONFIG = "config"
LEVEL = "level"
LOG_TO_FILE = "log_to_file"
FILENAME = "filename"
ENABLED = "enabled"
FORCE_CONSOLE = "force_console"


@callback
def async_register_api(opp: OpenPeerPower) -> None:
    """Register all of our api endpoints."""
    websocket_api.async_register_command(opp, websocket_network_status)
    websocket_api.async_register_command(opp, websocket_node_status)
    websocket_api.async_register_command(opp, websocket_add_node)
    websocket_api.async_register_command(opp, websocket_stop_inclusion)
    websocket_api.async_register_command(opp, websocket_remove_node)
    websocket_api.async_register_command(opp, websocket_stop_exclusion)
    websocket_api.async_register_command(opp, websocket_update_log_config)
    websocket_api.async_register_command(opp, websocket_get_log_config)
    websocket_api.async_register_command(opp, websocket_get_config_parameters)
    websocket_api.async_register_command(opp, websocket_set_config_parameter)
    opp.http.register_view(DumpView)  # type: ignore


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required(TYPE): "zwave_js/network_status", vol.Required(ENTRY_ID): str}
)
@callback
def websocket_network_status(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Get the status of the Z-Wave JS network."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    data = {
        "client": {
            "ws_server_url": client.ws_server_url,
            "state": "connected" if client.connected else "disconnected",
            "driver_version": client.version.driver_version,
            "server_version": client.version.server_version,
        },
        "controller": {
            "home_id": client.driver.controller.data["homeId"],
            "nodes": list(client.driver.controller.nodes),
        },
    }
    connection.send_result(
        msg[ID],
        data,
    )


@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/node_status",
        vol.Required(ENTRY_ID): str,
        vol.Required(NODE_ID): int,
    }
)
@callback
def websocket_node_status(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Get the status of a Z-Wave JS node."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    node_id = msg[NODE_ID]
    node = client.driver.controller.nodes.get(node_id)

    if node is None:
        connection.send_error(msg[ID], ERR_NOT_FOUND, f"Node {node_id} not found")
        return

    data = {
        "node_id": node.node_id,
        "is_routing": node.is_routing,
        "status": node.status,
        "is_secure": node.is_secure,
        "ready": node.ready,
    }
    connection.send_result(
        msg[ID],
        data,
    )


@websocket_api.require_admin  # type: ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/add_node",
        vol.Required(ENTRY_ID): str,
        vol.Optional("secure", default=False): bool,
    }
)
async def websocket_add_node(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Add a node to the Z-Wave network."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    controller = client.driver.controller
    include_non_secure = not msg["secure"]

    @callback
    def async_cleanup() -> None:
        """Remove signal listeners."""
        for unsub in unsubs:
            unsub()

    @callback
    def forward_event(event: dict) -> None:
        connection.send_message(
            websocket_api.event_message(msg[ID], {"event": event["event"]})
        )

    @callback
    def node_added(event: dict) -> None:
        node = event["node"]
        node_details = {
            "node_id": node.node_id,
            "status": node.status,
            "ready": node.ready,
        }
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": "node added", "node": node_details}
            )
        )

    @callback
    def device_registered(device: DeviceEntry) -> None:
        device_details = {"name": device.name, "id": device.id}
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": "device registered", "device": device_details}
            )
        )

    connection.subscriptions[msg["id"]] = async_cleanup
    unsubs = [
        controller.on("inclusion started", forward_event),
        controller.on("inclusion failed", forward_event),
        controller.on("inclusion stopped", forward_event),
        controller.on("node added", node_added),
        async_dispatcher_connect(
            opp, EVENT_DEVICE_ADDED_TO_REGISTRY, device_registered
        ),
    ]

    result = await controller.async_begin_inclusion(include_non_secure)
    connection.send_result(
        msg[ID],
        result,
    )


@websocket_api.require_admin  # type: ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/stop_inclusion",
        vol.Required(ENTRY_ID): str,
    }
)
async def websocket_stop_inclusion(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Cancel adding a node to the Z-Wave network."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    controller = client.driver.controller
    result = await controller.async_stop_inclusion()
    connection.send_result(
        msg[ID],
        result,
    )


@websocket_api.require_admin  # type: ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/stop_exclusion",
        vol.Required(ENTRY_ID): str,
    }
)
async def websocket_stop_exclusion(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Cancel removing a node from the Z-Wave network."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    controller = client.driver.controller
    result = await controller.async_stop_exclusion()
    connection.send_result(
        msg[ID],
        result,
    )


@websocket_api.require_admin  # type:ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/remove_node",
        vol.Required(ENTRY_ID): str,
    }
)
async def websocket_remove_node(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Remove a node from the Z-Wave network."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    controller = client.driver.controller

    @callback
    def async_cleanup() -> None:
        """Remove signal listeners."""
        for unsub in unsubs:
            unsub()

    @callback
    def forward_event(event: dict) -> None:
        connection.send_message(
            websocket_api.event_message(msg[ID], {"event": event["event"]})
        )

    @callback
    def node_removed(event: dict) -> None:
        node = event["node"]
        node_details = {
            "node_id": node.node_id,
        }

        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": "node removed", "node": node_details}
            )
        )

    connection.subscriptions[msg["id"]] = async_cleanup
    unsubs = [
        controller.on("exclusion started", forward_event),
        controller.on("exclusion failed", forward_event),
        controller.on("exclusion stopped", forward_event),
        controller.on("node removed", node_removed),
    ]

    result = await controller.async_begin_exclusion()
    connection.send_result(
        msg[ID],
        result,
    )


@websocket_api.require_admin  # type:ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/set_config_parameter",
        vol.Required(ENTRY_ID): str,
        vol.Required(NODE_ID): int,
        vol.Required(PROPERTY): int,
        vol.Optional(PROPERTY_KEY): int,
        vol.Required(VALUE): int,
    }
)
async def websocket_set_config_parameter(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Set a config parameter value for a Z-Wave node."""
    entry_id = msg[ENTRY_ID]
    node_id = msg[NODE_ID]
    property_ = msg[PROPERTY]
    property_key = msg.get(PROPERTY_KEY)
    value = msg[VALUE]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    node = client.driver.controller.nodes[node_id]
    try:
        result = await async_set_config_parameter(
            node, value, property_, property_key=property_key
        )
    except (InvalidNewValue, NotFoundError, NotImplementedError, SetValueFailed) as err:
        code = ERR_UNKNOWN_ERROR
        if isinstance(err, NotFoundError):
            code = ERR_NOT_FOUND
        elif isinstance(err, (InvalidNewValue, NotImplementedError)):
            code = ERR_NOT_SUPPORTED

        connection.send_error(
            msg[ID],
            code,
            str(err),
        )
        return

    connection.send_result(
        msg[ID],
        str(result),
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/get_config_parameters",
        vol.Required(ENTRY_ID): str,
        vol.Required(NODE_ID): int,
    }
)
@callback
def websocket_get_config_parameters(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Get a list of configuration parameters for a Z-Wave node."""
    entry_id = msg[ENTRY_ID]
    node_id = msg[NODE_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    node = client.driver.controller.nodes.get(node_id)

    if node is None:
        connection.send_error(msg[ID], ERR_NOT_FOUND, f"Node {node_id} not found")
        return

    values = node.get_configuration_values()
    result = {}
    for value_id, zwave_value in values.items():
        metadata = zwave_value.metadata
        result[value_id] = {
            "property": zwave_value.property_,
            "configuration_value_type": zwave_value.configuration_value_type.value,
            "metadata": {
                "description": metadata.description,
                "label": metadata.label,
                "type": metadata.type,
                "min": metadata.min,
                "max": metadata.max,
                "unit": metadata.unit,
                "writeable": metadata.writeable,
                "readable": metadata.readable,
            },
            "value": zwave_value.value,
        }
        if zwave_value.metadata.states:
            result[value_id]["metadata"]["states"] = zwave_value.metadata.states

    connection.send_result(
        msg[ID],
        result,
    )


def convert_log_level_to_enum(value: str) -> LogLevel:
    """Convert log level string to LogLevel enum."""
    return LogLevel[value.upper()]


def filename_is_present_if_logging_to_file(obj: Dict) -> Dict:
    """Validate that filename is provided if log_to_file is True."""
    if obj.get(LOG_TO_FILE, False) and FILENAME not in obj:
        raise vol.Invalid("`filename` must be provided if logging to file")
    return obj


@websocket_api.require_admin  # type: ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/update_log_config",
        vol.Required(ENTRY_ID): str,
        vol.Required(CONFIG): vol.All(
            vol.Schema(
                {
                    vol.Optional(ENABLED): cv.boolean,
                    vol.Optional(LEVEL): vol.All(
                        cv.string,
                        vol.Lower,
                        vol.In([log_level.name.lower() for log_level in LogLevel]),
                        lambda val: LogLevel[val.upper()],
                    ),
                    vol.Optional(LOG_TO_FILE): cv.boolean,
                    vol.Optional(FILENAME): cv.string,
                    vol.Optional(FORCE_CONSOLE): cv.boolean,
                }
            ),
            cv.has_at_least_one_key(
                ENABLED, FILENAME, FORCE_CONSOLE, LEVEL, LOG_TO_FILE
            ),
            filename_is_present_if_logging_to_file,
        ),
    },
)
async def websocket_update_log_config(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Update the driver log config."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    await client.driver.async_update_log_config(LogConfig(**msg[CONFIG]))
    connection.send_result(
        msg[ID],
    )


@websocket_api.require_admin  # type: ignore
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required(TYPE): "zwave_js/get_log_config",
        vol.Required(ENTRY_ID): str,
    },
)
async def websocket_get_log_config(
    opp: OpenPeerPower, connection: ActiveConnection, msg: dict
) -> None:
    """Get log configuration for the Z-Wave JS driver."""
    entry_id = msg[ENTRY_ID]
    client = opp.data[DOMAIN][entry_id][DATA_CLIENT]
    result = await client.driver.async_get_log_config()
    connection.send_result(
        msg[ID],
        dataclasses.asdict(result),
    )


class DumpView(OpenPeerPowerView):
    """View to dump the state of the Z-Wave JS server."""

    url = "/api/zwave_js/dump/{config_entry_id}"
    name = "api:zwave_js:dump"

    async def get(self, request: web.Request, config_entry_id: str) -> web.Response:
        """Dump the state of Z-Wave."""
        opp = request.app["opp"]

        if config_entry_id not in opp.data[DOMAIN]:
            raise web_exceptions.HTTPBadRequest

        entry = opp.config_entries.async_get_entry(config_entry_id)

        msgs = await dump.dump_msgs(entry.data[CONF_URL], async_get_clientsession(opp))

        return web.Response(
            body=json.dumps(msgs, indent=2) + "\n",
            headers={
                hdrs.CONTENT_TYPE: "application/json",
                hdrs.CONTENT_DISPOSITION: 'attachment; filename="zwave_js_dump.json"',
            },
        )
