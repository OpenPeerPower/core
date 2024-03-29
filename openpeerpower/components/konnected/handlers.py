"""Handle Konnected messages."""
import logging

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_STATE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
)
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.util import decorator

from .const import CONF_INVERSE, SIGNAL_DS18B20_NEW

_LOGGER = logging.getLogger(__name__)
HANDLERS = decorator.Registry()


@HANDLERS.register("state")
async def async_handle_state_update(opp, context, msg):
    """Handle a binary sensor or switch state update."""
    _LOGGER.debug("[state handler] context: %s  msg: %s", context, msg)
    entity_id = context.get(ATTR_ENTITY_ID)
    state = bool(int(msg.get(ATTR_STATE)))
    if context.get(CONF_INVERSE):
        state = not state

    async_dispatcher_send(opp, f"konnected.{entity_id}.update", state)


@HANDLERS.register("temp")
async def async_handle_temp_update(opp, context, msg):
    """Handle a temperature sensor state update."""
    _LOGGER.debug("[temp handler] context: %s  msg: %s", context, msg)
    entity_id, temp = context.get(DEVICE_CLASS_TEMPERATURE), msg.get("temp")
    if entity_id:
        async_dispatcher_send(opp, f"konnected.{entity_id}.update", temp)


@HANDLERS.register("humi")
async def async_handle_humi_update(opp, context, msg):
    """Handle a humidity sensor state update."""
    _LOGGER.debug("[humi handler] context: %s  msg: %s", context, msg)
    entity_id, humi = context.get(DEVICE_CLASS_HUMIDITY), msg.get("humi")
    if entity_id:
        async_dispatcher_send(opp, f"konnected.{entity_id}.update", humi)


@HANDLERS.register("addr")
async def async_handle_addr_update(opp, context, msg):
    """Handle an addressable sensor update."""
    _LOGGER.debug("[addr handler] context: %s  msg: %s", context, msg)
    addr, temp = msg.get("addr"), msg.get("temp")
    entity_id = context.get(addr)
    if entity_id:
        async_dispatcher_send(opp, f"konnected.{entity_id}.update", temp)
    else:
        msg["device_id"] = context.get("device_id")
        msg["temperature"] = temp
        msg["addr"] = addr
        async_dispatcher_send(opp, SIGNAL_DS18B20_NEW, msg)
