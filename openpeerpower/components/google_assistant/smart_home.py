"""Support for Google Assistant Smart Home API."""
import asyncio
from itertools import product
import logging

from openpeerpower.const import ATTR_ENTITY_ID, __version__
from openpeerpower.util.decorator import Registry

from .const import (
    ERR_DEVICE_OFFLINE,
    ERR_PROTOCOL_ERROR,
    ERR_UNKNOWN_ERROR,
    EVENT_COMMAND_RECEIVED,
    EVENT_QUERY_RECEIVED,
    EVENT_SYNC_RECEIVED,
)
from .error import SmartHomeError
from .helpers import GoogleEntity, RequestData, async_get_entities

HANDLERS = Registry()
_LOGGER = logging.getLogger(__name__)


async def async_handle_message(opp, config, user_id, message, source):
    """Handle incoming API messages."""
    data = RequestData(
        config, user_id, source, message["requestId"], message.get("devices")
    )

    response = await _process(opp, data, message)

    if response and "errorCode" in response["payload"]:
        _LOGGER.error("Error handling message %s: %s", message, response["payload"])

    return response


async def _process(opp, data, message):
    """Process a message."""
    inputs: list = message.get("inputs")

    if len(inputs) != 1:
        return {
            "requestId": data.request_id,
            "payload": {"errorCode": ERR_PROTOCOL_ERROR},
        }

    handler = HANDLERS.get(inputs[0].get("intent"))

    if handler is None:
        return {
            "requestId": data.request_id,
            "payload": {"errorCode": ERR_PROTOCOL_ERROR},
        }

    try:
        result = await handler(opp, data, inputs[0].get("payload"))
    except SmartHomeError as err:
        return {"requestId": data.request_id, "payload": {"errorCode": err.code}}
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error")
        return {
            "requestId": data.request_id,
            "payload": {"errorCode": ERR_UNKNOWN_ERROR},
        }

    if result is None:
        return None

    return {"requestId": data.request_id, "payload": result}


@HANDLERS.register("action.devices.SYNC")
async def async_devices_sync(opp, data, payload):
    """Handle action.devices.SYNC request.

    https://developers.google.com/assistant/smarthome/develop/process-intents#SYNC
    """
    opp.bus.async_fire(
        EVENT_SYNC_RECEIVED,
        {"request_id": data.request_id, "source": data.source},
        context=data.context,
    )

    agent_user_id = data.config.get_agent_user_id(data.context)
    entities = async_get_entities(opp, data.config)
    results = await asyncio.gather(
        *(
            entity.sync_serialize(agent_user_id)
            for entity in entities
            if entity.should_expose()
        ),
        return_exceptions=True,
    )

    devices = []

    for entity, result in zip(entities, results):
        if isinstance(result, Exception):
            _LOGGER.error("Error serializing %s", entity.entity_id, exc_info=result)
        else:
            devices.append(result)

    response = {"agentUserId": agent_user_id, "devices": devices}

    await data.config.async_connect_agent_user(agent_user_id)

    _LOGGER.debug("Syncing entities response: %s", response)

    return response


@HANDLERS.register("action.devices.QUERY")
async def async_devices_query(opp, data, payload):
    """Handle action.devices.QUERY request.

    https://developers.google.com/assistant/smarthome/develop/process-intents#QUERY
    """
    devices = {}
    for device in payload.get("devices", []):
        devid = device["id"]
        state = opp.states.get(devid)

        opp.bus.async_fire(
            EVENT_QUERY_RECEIVED,
            {
                "request_id": data.request_id,
                ATTR_ENTITY_ID: devid,
                "source": data.source,
            },
            context=data.context,
        )

        if not state:
            # If we can't find a state, the device is offline
            devices[devid] = {"online": False}
            continue

        entity = GoogleEntity(opp, data.config, state)
        try:
            devices[devid] = entity.query_serialize()
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error serializing query for %s", state)
            devices[devid] = {"online": False}

    return {"devices": devices}


async def _entity_execute(entity, data, executions):
    """Execute all commands for an entity.

    Returns a dict if a special result needs to be set.
    """
    for execution in executions:
        try:
            await entity.execute(data, execution)
        except SmartHomeError as err:
            return {
                "ids": [entity.entity_id],
                "status": "ERROR",
                **err.to_response(),
            }

    return None


@HANDLERS.register("action.devices.EXECUTE")
async def handle_devices_execute(opp, data, payload):
    """Handle action.devices.EXECUTE request.

    https://developers.google.com/assistant/smarthome/develop/process-intents#EXECUTE
    """
    entities = {}
    executions = {}
    results = {}

    for command in payload["commands"]:
        for device, execution in product(command["devices"], command["execution"]):
            entity_id = device["id"]

            opp.bus.async_fire(
                EVENT_COMMAND_RECEIVED,
                {
                    "request_id": data.request_id,
                    ATTR_ENTITY_ID: entity_id,
                    "execution": execution,
                    "source": data.source,
                },
                context=data.context,
            )

            # Happens if error occurred. Skip entity for further processing
            if entity_id in results:
                continue

            if entity_id in entities:
                executions[entity_id].append(execution)
                continue

            state = opp.states.get(entity_id)

            if state is None:
                results[entity_id] = {
                    "ids": [entity_id],
                    "status": "ERROR",
                    "errorCode": ERR_DEVICE_OFFLINE,
                }
                continue

            entities[entity_id] = GoogleEntity(opp, data.config, state)
            executions[entity_id] = [execution]

    execute_results = await asyncio.gather(
        *[
            _entity_execute(entities[entity_id], data, executions[entity_id])
            for entity_id in executions
        ]
    )

    for entity_id, result in zip(executions, execute_results):
        if result is not None:
            results[entity_id] = result

    final_results = list(results.values())

    for entity in entities.values():
        if entity.entity_id in results:
            continue

        entity.async_update()

        final_results.append(
            {
                "ids": [entity.entity_id],
                "status": "SUCCESS",
                "states": entity.query_serialize(),
            }
        )

    return {"commands": final_results}


@HANDLERS.register("action.devices.DISCONNECT")
async def async_devices_disconnect(opp, data: RequestData, payload):
    """Handle action.devices.DISCONNECT request.

    https://developers.google.com/assistant/smarthome/develop/process-intents#DISCONNECT
    """
    await data.config.async_disconnect_agent_user(data.context.user_id)
    return None


@HANDLERS.register("action.devices.IDENTIFY")
async def async_devices_identify(opp, data: RequestData, payload):
    """Handle action.devices.IDENTIFY request.

    https://developers.google.com/assistant/smarthome/develop/local#implement_the_identify_handler
    """
    return {
        "device": {
            "id": data.config.get_agent_user_id(data.context),
            "isLocalOnly": True,
            "isProxy": True,
            "deviceInfo": {
                "hwVersion": "UNKNOWN_HW_VERSION",
                "manufacturer": "Open Peer Power",
                "model": "Open Peer Power",
                "swVersion": __version__,
            },
        }
    }


@HANDLERS.register("action.devices.REACHABLE_DEVICES")
async def async_devices_reachable(opp, data: RequestData, payload):
    """Handle action.devices.REACHABLE_DEVICES request.

    https://developers.google.com/actions/smarthome/create#actiondevicesdisconnect
    """
    google_ids = {dev["id"] for dev in (data.devices or [])}

    return {
        "devices": [
            entity.reachable_device_serialize()
            for entity in async_get_entities(opp, data.config)
            if entity.entity_id in google_ids and entity.should_expose_local()
        ]
    }


def turned_off_response(message):
    """Return a device turned off response."""
    return {
        "requestId": message.get("requestId"),
        "payload": {"errorCode": "deviceTurnedOff"},
    }
