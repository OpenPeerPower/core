"""Alexa state report code."""
import asyncio
import json
import logging
from typing import Optional

import aiohttp
import async_timeout

from openpeerpower.const import HTTP_ACCEPTED, MATCH_ALL, STATE_ON
from openpeerpower.core import OpenPeerPower, State, callback
from openpeerpower.helpers.significant_change import create_checker
import openpeerpower.util.dt as dt_util

from .const import API_CHANGE, DOMAIN, Cause
from .entities import ENTITY_ADAPTERS, AlexaEntity, generate_alexa_id
from .messages import AlexaResponse

_LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 10


async def async_enable_proactive_mode.opp, smart_home_config):
    """Enable the proactive mode.

    Proactive mode makes this component report state changes to Alexa.
    """
    # Validate we can get access token.
    await smart_home_config.async_get_access_token()

    @callback
    def extra_significant_check(
        opp: OpenPeerPower,
        old_state: str,
        old_attrs: dict,
        old_extra_arg: dict,
        new_state: str,
        new_attrs: dict,
        new_extra_arg: dict,
    ):
        """Check if the serialized data has changed."""
        return old_extra_arg is not None and old_extra_arg != new_extra_arg

    checker = await create_checker.opp, DOMAIN, extra_significant_check)

    async def async_entity_state_listener(
        changed_entity: str,
        old_state: Optional[State],
        new_state: Optional[State],
    ):
        if not.opp.is_running:
            return

        if not new_state:
            return

        if new_state.domain not in ENTITY_ADAPTERS:
            return

        if not smart_home_config.should_expose(changed_entity):
            _LOGGER.debug("Not exposing %s because filtered by config", changed_entity)
            return

        alexa_changed_entity: AlexaEntity = ENTITY_ADAPTERS[new_state.domain](
           .opp, smart_home_config, new_state
        )

        # Determine how entity should be reported on
        should_report = False
        should_doorbell = False

        for interface in alexa_changed_entity.interfaces():
            if not should_report and interface.properties_proactively_reported():
                should_report = True

            if (
                interface.name() == "Alexa.DoorbellEventSource"
                and new_state.state == STATE_ON
            ):
                should_doorbell = True
                break

        if not should_report and not should_doorbell:
            return

        if should_doorbell:
            should_report = False

        if should_report:
            alexa_properties = list(alexa_changed_entity.serialize_properties())
        else:
            alexa_properties = None

        if not checker.async_is_significant_change(
            new_state, extra_arg=alexa_properties
        ):
            return

        if should_report:
            await async_send_changereport_message(
               .opp, smart_home_config, alexa_changed_entity, alexa_properties
            )

        elif should_doorbell:
            await async_send_doorbell_event_message(
               .opp, smart_home_config, alexa_changed_entity
            )

    return.opp.helpers.event.async_track_state_change(
        MATCH_ALL, async_entity_state_listener
    )


async def async_send_changereport_message(
   .opp, config, alexa_entity, alexa_properties, *, invalidate_access_token=True
):
    """Send a ChangeReport message for an Alexa entity.

    https://developer.amazon.com/docs/smarthome/state-reporting-for-a-smart-home-skill.html#report-state-with-changereport-events
    """
    token = await config.async_get_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    endpoint = alexa_entity.alexa_id()

    payload = {
        API_CHANGE: {
            "cause": {"type": Cause.APP_INTERACTION},
            "properties": alexa_properties,
        }
    }

    message = AlexaResponse(name="ChangeReport", namespace="Alexa", payload=payload)
    message.set_endpoint_full(token, endpoint)

    message_serialized = message.serialize()
    session =.opp.helpers.aiohttp_client.async_get_clientsession()

    try:
        with async_timeout.timeout(DEFAULT_TIMEOUT):
            response = await session.post(
                config.endpoint,
                headers=headers,
                json=message_serialized,
                allow_redirects=True,
            )

    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.error("Timeout sending report to Alexa")
        return

    response_text = await response.text()

    _LOGGER.debug("Sent: %s", json.dumps(message_serialized))
    _LOGGER.debug("Received (%s): %s", response.status, response_text)

    if response.status == HTTP_ACCEPTED:
        return

    response_json = json.loads(response_text)

    if (
        response_json["payload"]["code"] == "INVALID_ACCESS_TOKEN_EXCEPTION"
        and not invalidate_access_token
    ):
        config.async_invalidate_access_token()
        return await async_send_changereport_message(
           .opp, config, alexa_entity, alexa_properties, invalidate_access_token=False
        )

    _LOGGER.error(
        "Error when sending ChangeReport to Alexa: %s: %s",
        response_json["payload"]["code"],
        response_json["payload"]["description"],
    )


async def async_send_add_or_update_message.opp, config, entity_ids):
    """Send an AddOrUpdateReport message for entities.

    https://developer.amazon.com/docs/device-apis/alexa-discovery.html#add-or-update-report
    """
    token = await config.async_get_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    endpoints = []

    for entity_id in entity_ids:
        domain = entity_id.split(".", 1)[0]

        if domain not in ENTITY_ADAPTERS:
            continue

        alexa_entity = ENTITY_ADAPTERS[domain].opp, config, opp.states.get(entity_id))
        endpoints.append(alexa_entity.serialize_discovery())

    payload = {"endpoints": endpoints, "scope": {"type": "BearerToken", "token": token}}

    message = AlexaResponse(
        name="AddOrUpdateReport", namespace="Alexa.Discovery", payload=payload
    )

    message_serialized = message.serialize()
    session =.opp.helpers.aiohttp_client.async_get_clientsession()

    return await session.post(
        config.endpoint, headers=headers, json=message_serialized, allow_redirects=True
    )


async def async_send_delete_message.opp, config, entity_ids):
    """Send an DeleteReport message for entities.

    https://developer.amazon.com/docs/device-apis/alexa-discovery.html#deletereport-event
    """
    token = await config.async_get_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    endpoints = []

    for entity_id in entity_ids:
        domain = entity_id.split(".", 1)[0]

        if domain not in ENTITY_ADAPTERS:
            continue

        endpoints.append({"endpointId": generate_alexa_id(entity_id)})

    payload = {"endpoints": endpoints, "scope": {"type": "BearerToken", "token": token}}

    message = AlexaResponse(
        name="DeleteReport", namespace="Alexa.Discovery", payload=payload
    )

    message_serialized = message.serialize()
    session =.opp.helpers.aiohttp_client.async_get_clientsession()

    return await session.post(
        config.endpoint, headers=headers, json=message_serialized, allow_redirects=True
    )


async def async_send_doorbell_event_message.opp, config, alexa_entity):
    """Send a DoorbellPress event message for an Alexa entity.

    https://developer.amazon.com/docs/smarthome/send-events-to-the-alexa-event-gateway.html
    """
    token = await config.async_get_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    endpoint = alexa_entity.alexa_id()

    message = AlexaResponse(
        name="DoorbellPress",
        namespace="Alexa.DoorbellEventSource",
        payload={
            "cause": {"type": Cause.PHYSICAL_INTERACTION},
            "timestamp": f"{dt_util.utcnow().replace(tzinfo=None).isoformat()}Z",
        },
    )

    message.set_endpoint_full(token, endpoint)

    message_serialized = message.serialize()
    session =.opp.helpers.aiohttp_client.async_get_clientsession()

    try:
        with async_timeout.timeout(DEFAULT_TIMEOUT):
            response = await session.post(
                config.endpoint,
                headers=headers,
                json=message_serialized,
                allow_redirects=True,
            )

    except (asyncio.TimeoutError, aiohttp.ClientError):
        _LOGGER.error("Timeout sending report to Alexa")
        return

    response_text = await response.text()

    _LOGGER.debug("Sent: %s", json.dumps(message_serialized))
    _LOGGER.debug("Received (%s): %s", response.status, response_text)

    if response.status == HTTP_ACCEPTED:
        return

    response_json = json.loads(response_text)

    _LOGGER.error(
        "Error when sending DoorbellPress event to Alexa: %s: %s",
        response_json["payload"]["code"],
        response_json["payload"]["description"],
    )
