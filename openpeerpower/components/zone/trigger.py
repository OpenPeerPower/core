"""Offer zone automation rules."""
import voluptuous as vol

from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    CONF_ENTITY_ID,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_ZONE,
)
from openpeerpower.core import CALLBACK_TYPE, OppJob, callback
from openpeerpower.helpers import condition, config_validation as cv, location
from openpeerpower.helpers.event import async_track_state_change_event

# mypy: allow-incomplete-defs, allow-untyped-defs
# mypy: no-check-untyped-defs

EVENT_ENTER = "enter"
EVENT_LEAVE = "leave"
DEFAULT_EVENT = EVENT_ENTER

_EVENT_DESCRIPTION = {EVENT_ENTER: "entering", EVENT_LEAVE: "leaving"}

TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): "zone",
        vol.Required(CONF_ENTITY_ID): cv.entity_ids,
        vol.Required(CONF_ZONE): cv.entity_id,
        vol.Required(CONF_EVENT, default=DEFAULT_EVENT): vol.Any(
            EVENT_ENTER, EVENT_LEAVE
        ),
    }
)


async def async_attach_trigger(
    opp, config, action, automation_info, *, platform_type: str = "zone"
) -> CALLBACK_TYPE:
    """Listen for state changes based on configuration."""
    entity_id = config.get(CONF_ENTITY_ID)
    zone_entity_id = config.get(CONF_ZONE)
    event = config.get(CONF_EVENT)
    job = OppJob(action)

    @callback
    def zone_automation_listener(zone_event):
        """Listen for state changes and calls action."""
        entity = zone_event.data.get("entity_id")
        from_s = zone_event.data.get("old_state")
        to_s = zone_event.data.get("new_state")

        if (
            from_s
            and not location.has_location(from_s)
            or not location.has_location(to_s)
        ):
            return

        zone_state = opp.states.get(zone_entity_id)
        from_match = condition.zone(opp, zone_state, from_s) if from_s else False
        to_match = condition.zone(opp, zone_state, to_s) if to_s else False

        if (
            event == EVENT_ENTER
            and not from_match
            and to_match
            or event == EVENT_LEAVE
            and from_match
            and not to_match
        ):
            description = f"{entity} {_EVENT_DESCRIPTION[event]} {zone_state.attributes[ATTR_FRIENDLY_NAME]}"
            opp.async_run_opp_job(
                job,
                {
                    "trigger": {
                        "platform": platform_type,
                        "entity_id": entity,
                        "from_state": from_s,
                        "to_state": to_s,
                        "zone": zone_state,
                        "event": event,
                        "description": description,
                    }
                },
                to_s.context,
            )

    return async_track_state_change_event(opp, entity_id, zone_automation_listener)
