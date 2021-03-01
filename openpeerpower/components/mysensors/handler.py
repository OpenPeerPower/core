"""Handle MySensors messages."""
from typing import Dict, List

from mysensors import Message

from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util import decorator

from .const import (
    CHILD_CALLBACK,
    DOMAIN,
    MYSENSORS_GATEWAY_READY,
    NODE_CALLBACK,
    DevId,
    GatewayId,
)
from .device import get_mysensors_devices
from .helpers import discover_mysensors_platform, validate_set_msg

HANDLERS = decorator.Registry()


@HANDLERS.register("set")
async def handle_set(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle a mysensors set message."""
    validated = validate_set_msg(gateway_id, msg)
    _handle_child_update(opp, gateway_id, validated)


@HANDLERS.register("internal")
async def handle_internal(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle a mysensors internal message."""
    internal = msg.gateway.const.Internal(msg.sub_type)
    handler = HANDLERS.get(internal.name)
    if handler is None:
        return
    await handler(opp, gateway_id, msg)


@HANDLERS.register("I_BATTERY_LEVEL")
async def handle_battery_level(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle an internal battery level message."""
    _handle_node_update(opp, gateway_id, msg)


@HANDLERS.register("I_HEARTBEAT_RESPONSE")
async def handle_heartbeat(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle an heartbeat."""
    _handle_node_update(opp, gateway_id, msg)


@HANDLERS.register("I_SKETCH_NAME")
async def handle_sketch_name(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle an internal sketch name message."""
    _handle_node_update(opp, gateway_id, msg)


@HANDLERS.register("I_SKETCH_VERSION")
async def handle_sketch_version(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle an internal sketch version message."""
    _handle_node_update(opp, gateway_id, msg)


@HANDLERS.register("I_GATEWAY_READY")
async def handle_gateway_ready(
    opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message
) -> None:
    """Handle an internal gateway ready message.

    Set asyncio future result if gateway is ready.
    """
    gateway_ready = opp.data[DOMAIN].get(MYSENSORS_GATEWAY_READY.format(gateway_id))
    if gateway_ready is None or gateway_ready.cancelled():
        return
    gateway_ready.set_result(True)


@callback
def _handle_child_update(
    opp: OpenPeerPowerType, gateway_id: GatewayId, validated: Dict[str, List[DevId]]
):
    """Handle a child update."""
    signals: List[str] = []

    # Update all platforms for the device via dispatcher.
    # Add/update entity for validated children.
    for platform, dev_ids in validated.items():
        devices = get_mysensors_devices(opp, platform)
        new_dev_ids: List[DevId] = []
        for dev_id in dev_ids:
            if dev_id in devices:
                signals.append(CHILD_CALLBACK.format(*dev_id))
            else:
                new_dev_ids.append(dev_id)
        if new_dev_ids:
            discover_mysensors_platform(opp, gateway_id, platform, new_dev_ids)
    for signal in set(signals):
        # Only one signal per device is needed.
        # A device can have multiple platforms, ie multiple schemas.
        async_dispatcher_send(opp, signal)


@callback
def _handle_node_update(opp: OpenPeerPowerType, gateway_id: GatewayId, msg: Message):
    """Handle a node update."""
    signal = NODE_CALLBACK.format(gateway_id, msg.node_id)
    async_dispatcher_send(opp, signal)
