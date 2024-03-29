"""The Netatmo integration."""
import logging

from openpeerpower.const import ATTR_DEVICE_ID, ATTR_ID, ATTR_NAME
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_EVENT_TYPE,
    ATTR_FACE_URL,
    ATTR_IS_KNOWN,
    ATTR_PERSONS,
    DATA_DEVICE_IDS,
    DATA_PERSONS,
    DEFAULT_PERSON,
    DOMAIN,
    EVENT_ID_MAP,
    NETATMO_EVENT,
)

_LOGGER = logging.getLogger(__name__)

SUBEVENT_TYPE_MAP = {
    "outdoor": "",
    "therm_mode": "",
}


async def async_handle_webhook(opp, webhook_id, request):
    """Handle webhook callback."""
    try:
        data = await request.json()
    except ValueError as err:
        _LOGGER.error("Error in data: %s", err)
        return None

    _LOGGER.debug("Got webhook data: %s", data)

    event_type = data.get(ATTR_EVENT_TYPE)

    if event_type in SUBEVENT_TYPE_MAP:
        async_send_event(opp, event_type, data)

        for event_data in data.get(SUBEVENT_TYPE_MAP[event_type], []):
            async_evaluate_event(opp, event_data)

    else:
        async_evaluate_event(opp, data)


def async_evaluate_event(opp, event_data):
    """Evaluate events from webhook."""
    event_type = event_data.get(ATTR_EVENT_TYPE)

    if event_type == "person":
        for person in event_data.get(ATTR_PERSONS):
            person_event_data = dict(event_data)
            person_event_data[ATTR_ID] = person.get(ATTR_ID)
            person_event_data[ATTR_NAME] = opp.data[DOMAIN][DATA_PERSONS].get(
                person_event_data[ATTR_ID], DEFAULT_PERSON
            )
            person_event_data[ATTR_IS_KNOWN] = person.get(ATTR_IS_KNOWN)
            person_event_data[ATTR_FACE_URL] = person.get(ATTR_FACE_URL)

            async_send_event(opp, event_type, person_event_data)

    else:
        async_send_event(opp, event_type, event_data)


def async_send_event(opp, event_type, data):
    """Send events."""
    _LOGGER.debug("%s: %s", event_type, data)
    async_dispatcher_send(
        opp,
        f"signal-{DOMAIN}-webhook-{event_type}",
        {"type": event_type, "data": data},
    )

    event_data = {
        "type": event_type,
        "data": data,
    }

    if event_type in EVENT_ID_MAP:
        data_device_id = data[EVENT_ID_MAP[event_type]]
        event_data[ATTR_DEVICE_ID] = opp.data[DOMAIN][DATA_DEVICE_IDS].get(
            data_device_id
        )

    opp.bus.async_fire(
        event_type=NETATMO_EVENT,
        event_data=event_data,
    )
