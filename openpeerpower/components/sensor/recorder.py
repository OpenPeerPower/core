"""Statistics helper for sensor."""
from __future__ import annotations

import datetime
import itertools

from openpeerpower.components.recorder import history, statistics
from openpeerpower.components.sensor import (
    ATTR_STATE_CLASS,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    STATE_CLASS_MEASUREMENT,
)
from openpeerpower.const import ATTR_DEVICE_CLASS
from openpeerpower.core import OpenPeerPower, State
import openpeerpower.util.dt as dt_util

from . import DOMAIN

DEVICE_CLASS_STATISTICS = {
    DEVICE_CLASS_BATTERY: {"mean", "min", "max"},
    DEVICE_CLASS_ENERGY: {"sum"},
    DEVICE_CLASS_HUMIDITY: {"mean", "min", "max"},
    DEVICE_CLASS_PRESSURE: {"mean", "min", "max"},
    DEVICE_CLASS_TEMPERATURE: {"mean", "min", "max"},
}


def _get_entities(opp: OpenPeerPower) -> list[tuple[str, str]]:
    """Get (entity_id, device_class) of all sensors for which to compile statistics."""
    all_sensors = opp.states.all(DOMAIN)
    entity_ids = []

    for state in all_sensors:
        device_class = state.attributes.get(ATTR_DEVICE_CLASS)
        state_class = state.attributes.get(ATTR_STATE_CLASS)
        if not state_class or state_class != STATE_CLASS_MEASUREMENT:
            continue
        if not device_class or device_class not in DEVICE_CLASS_STATISTICS:
            continue
        entity_ids.append((state.entity_id, device_class))
    return entity_ids


# Faster than try/except
# From https://stackoverflow.com/a/23639915
def _is_number(s: str) -> bool:  # pylint: disable=invalid-name
    """Return True if string is a number."""
    return s.replace(".", "", 1).isdigit()


def _time_weighted_average(
    fstates: list[tuple[float, State]], start: datetime.datetime, end: datetime.datetime
) -> float:
    """Calculate a time weighted average.

    The average is calculated by, weighting the states by duration in seconds between
    state changes.
    Note: there's no interpolation of values between state changes.
    """
    old_fstate: float | None = None
    old_start_time: datetime.datetime | None = None
    accumulated = 0.0

    for fstate, state in fstates:
        # The recorder will give us the last known state, which may be well
        # before the requested start time for the statistics
        start_time = start if state.last_updated < start else state.last_updated
        if old_start_time is None:
            # Adjust start time, if there was no last known state
            start = start_time
        else:
            duration = start_time - old_start_time
            # Accumulate the value, weighted by duration until next state change
            assert old_fstate is not None
            accumulated += old_fstate * duration.total_seconds()

        old_fstate = fstate
        old_start_time = start_time

    if old_fstate is not None:
        # Accumulate the value, weighted by duration until end of the period
        assert old_start_time is not None
        duration = end - old_start_time
        accumulated += old_fstate * duration.total_seconds()

    return accumulated / (end - start).total_seconds()


def compile_statistics(
    opp: OpenPeerPower, start: datetime.datetime, end: datetime.datetime
) -> dict:
    """Compile statistics for all entities during start-end.

    Note: This will query the database and must not be run in the event loop
    """
    result: dict = {}

    entities = _get_entities(opp)

    # Get history between start and end
    history_list = history.get_significant_states(  # type: ignore
        opp, start - datetime.timedelta.resolution, end, [i[0] for i in entities]
    )

    for entity_id, device_class in entities:
        wanted_statistics = DEVICE_CLASS_STATISTICS[device_class]

        if entity_id not in history_list:
            continue

        entity_history = history_list[entity_id]
        fstates = [
            (float(el.state), el) for el in entity_history if _is_number(el.state)
        ]

        if not fstates:
            continue

        result[entity_id] = {}

        # Make calculations
        if "max" in wanted_statistics:
            result[entity_id]["max"] = max(*itertools.islice(zip(*fstates), 1))
        if "min" in wanted_statistics:
            result[entity_id]["min"] = min(*itertools.islice(zip(*fstates), 1))

        if "mean" in wanted_statistics:
            result[entity_id]["mean"] = _time_weighted_average(fstates, start, end)

        if "sum" in wanted_statistics:
            last_reset = old_last_reset = None
            new_state = old_state = None
            _sum = 0
            last_stats = statistics.get_last_statistics(opp, 1, entity_id)  # type: ignore
            if entity_id in last_stats:
                # We have compiled history for this sensor before, use that as a starting point
                last_reset = old_last_reset = last_stats[entity_id][0]["last_reset"]
                new_state = old_state = last_stats[entity_id][0]["state"]
                _sum = last_stats[entity_id][0]["sum"]

            for fstate, state in fstates:
                if "last_reset" not in state.attributes:
                    continue
                if (last_reset := state.attributes["last_reset"]) != old_last_reset:
                    # The sensor has been reset, update the sum
                    if old_state is not None:
                        _sum += new_state - old_state
                    # ..and update the starting point
                    new_state = fstate
                    old_last_reset = last_reset
                    old_state = new_state
                else:
                    new_state = fstate

            if last_reset is None or new_state is None or old_state is None:
                # No valid updates
                result.pop(entity_id)
                continue

            # Update the sum with the last state
            _sum += new_state - old_state
            result[entity_id]["last_reset"] = dt_util.parse_datetime(last_reset)
            result[entity_id]["sum"] = _sum
            result[entity_id]["state"] = new_state

    return result
