"""Offer time listening automation rules."""
from datetime import datetime
from functools import partial

import voluptuous as vol

from openpeerpower.components import sensor
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    CONF_AT,
    CONF_PLATFORM,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from openpeerpower.core import OppJob, callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_time_change,
)
import openpeerpower.util.dt as dt_util

# mypy: allow-untyped-defs, no-check-untyped-defs

_TIME_TRIGGER_SCHEMA = vol.Any(
    cv.time,
    vol.All(str, cv.entity_domain(("input_datetime", "sensor"))),
    msg="Expected HH:MM, HH:MM:SS or Entity ID with domain 'input_datetime' or 'sensor'",
)

TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): "time",
        vol.Required(CONF_AT): vol.All(cv.ensure_list, [_TIME_TRIGGER_SCHEMA]),
    }
)


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for state changes based on configuration."""
    trigger_id = automation_info.get("trigger_id") if automation_info else None
    entities = {}
    removes = []
    job = OppJob(action)

    @callback
    def time_automation_listener(description, now, *, entity_id=None):
        """Listen for time changes and calls action."""
        opp.async_run_opp_job(
            job,
            {
                "trigger": {
                    "platform": "time",
                    "now": now,
                    "description": description,
                    "entity_id": entity_id,
                    "id": trigger_id,
                }
            },
        )

    @callback
    def update_entity_trigger_event(event):
        """update_entity_trigger from the event."""
        return update_entity_trigger(event.data["entity_id"], event.data["new_state"])

    @callback
    def update_entity_trigger(entity_id, new_state=None):
        """Update the entity trigger for the entity_id."""
        # If a listener was already set up for entity, remove it.
        remove = entities.pop(entity_id, None)
        if remove:
            remove()
            remove = None

        if not new_state:
            return

        # Check state of entity. If valid, set up a listener.
        if new_state.domain == "input_datetime":
            has_date = new_state.attributes["has_date"]
            if has_date:
                year = new_state.attributes["year"]
                month = new_state.attributes["month"]
                day = new_state.attributes["day"]
            has_time = new_state.attributes["has_time"]
            if has_time:
                hour = new_state.attributes["hour"]
                minute = new_state.attributes["minute"]
                second = new_state.attributes["second"]
            else:
                # If no time then use midnight.
                hour = minute = second = 0

            if has_date:
                # If input_datetime has date, then track point in time.
                trigger_dt = datetime(
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    tzinfo=dt_util.DEFAULT_TIME_ZONE,
                )
                # Only set up listener if time is now or in the future.
                if trigger_dt >= dt_util.now():
                    remove = async_track_point_in_time(
                        opp,
                        partial(
                            time_automation_listener,
                            f"time set in {entity_id}",
                            entity_id=entity_id,
                        ),
                        trigger_dt,
                    )
            elif has_time:
                # Else if it has time, then track time change.
                remove = async_track_time_change(
                    opp,
                    partial(
                        time_automation_listener,
                        f"time set in {entity_id}",
                        entity_id=entity_id,
                    ),
                    hour=hour,
                    minute=minute,
                    second=second,
                )
        elif (
            new_state.domain == "sensor"
            and new_state.attributes.get(ATTR_DEVICE_CLASS)
            == sensor.DEVICE_CLASS_TIMESTAMP
            and new_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        ):
            trigger_dt = dt_util.parse_datetime(new_state.state)

            if trigger_dt is not None and trigger_dt > dt_util.utcnow():
                remove = async_track_point_in_time(
                    opp,
                    partial(
                        time_automation_listener,
                        f"time set in {entity_id}",
                        entity_id=entity_id,
                    ),
                    trigger_dt,
                )

        # Was a listener set up?
        if remove:
            entities[entity_id] = remove

    to_track = []

    for at_time in config[CONF_AT]:
        if isinstance(at_time, str):
            # entity
            to_track.append(at_time)
            update_entity_trigger(at_time, new_state=opp.states.get(at_time))
        else:
            # datetime.time
            removes.append(
                async_track_time_change(
                    opp,
                    partial(time_automation_listener, "time"),
                    hour=at_time.hour,
                    minute=at_time.minute,
                    second=at_time.second,
                )
            )

    # Track state changes of any entities.
    removes.append(
        async_track_state_change_event(opp, to_track, update_entity_trigger_event)
    )

    @callback
    def remove_track_time_changes():
        """Remove tracked time changes."""
        for remove in entities.values():
            remove()
        for remove in removes:
            remove()

    return remove_track_time_changes
