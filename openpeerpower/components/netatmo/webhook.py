"""The Netatmo integration."""
import logging

from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_EVENT_TYPE,
    ATTR_FACE_URL,
    ATTR_ID,
    ATTR_IS_KNOWN,
    ATTR_NAME,
    ATTR_PERSONS,
    DATA_PERSONS,
    DEFAULT_PERSON,
    DOMAIN,
    NETATMO_EVENT,
)

_LOGGER = logging.getLogger(__name__)

EVENT_TYPE_MAP = {
    "outdoor": "",
    "therm_mode": "",
}


async def handle_webhook.opp, webhook_id, request):
    """Handle webhook callback."""
    try:
        data = await request.json()
    except ValueError as err:
        _LOGGER.error("Error in data: %s", err)
        return None

    _LOGGER.debug("Got webhook data: %s", data)

    event_type = data.get(ATTR_EVENT_TYPE)

    if event_type in EVENT_TYPE_MAP:
        async_send_event.opp, event_type, data)

        for event_data in data.get(EVENT_TYPE_MAP[event_type], []):
            async_evaluate_event.opp, event_data)

    else:
        async_evaluate_event.opp, data)


@callback
def async_evaluate_event.opp, event_data):
    """Evaluate events from webhook."""
    event_type = event_data.get(ATTR_EVENT_TYPE)

    if event_type == "person":
        for person in event_data.get(ATTR_PERSONS):
            person_event_data = dict(event_data)
            person_event_data[ATTR_ID] = person.get(ATTR_ID)
            person_event_data[ATTR_NAME] =.opp.data[DOMAIN][DATA_PERSONS].get(
                person_event_data[ATTR_ID], DEFAULT_PERSON
            )
            person_event_data[ATTR_IS_KNOWN] = person.get(ATTR_IS_KNOWN)
            person_event_data[ATTR_FACE_URL] = person.get(ATTR_FACE_URL)

            async_send_event.opp, event_type, person_event_data)

    else:
        _LOGGER.debug("%s: %s", event_type, event_data)
        async_send_event.opp, event_type, event_data)


@callback
def async_send_event.opp, event_type, data):
    """Send events."""
   .opp.bus.async_fire(
        event_type=NETATMO_EVENT, event_data={"type": event_type, "data": data}
    )
    async_dispatcher_send(
       .opp,
        f"signal-{DOMAIN}-webhook-{event_type}",
        {"type": event_type, "data": data},
    )
