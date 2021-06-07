"""Helpers for Waze Travel Time integration."""
import re

from WazeRouteCalculator import WazeRouteCalculator, WRCError

from openpeerpower.components.waze_travel_time.const import ENTITY_ID_PATTERN
from openpeerpower.const import ATTR_LATITUDE, ATTR_LONGITUDE
from openpeerpower.helpers import location


def is_valid_config_entry(opp, logger, origin, destination, region):
    """Return whether the config entry data is valid."""
    origin = resolve_location(opp, logger, origin)
    destination = resolve_location(opp, logger, destination)
    try:
        WazeRouteCalculator(origin, destination, region).calc_all_routes_info()
    except WRCError:
        return False
    return True


def resolve_location(opp, logger, loc):
    """Resolve a location."""
    if re.fullmatch(ENTITY_ID_PATTERN, loc):
        return get_location_from_entity(opp, logger, loc)

    return resolve_zone(opp, loc)


def get_location_from_entity(opp, logger, entity_id):
    """Get the location from the entity_id."""
    state = opp.states.get(entity_id)

    if state is None:
        logger.error("Unable to find entity %s", entity_id)
        return None

    # Check if the entity has location attributes.
    if location.has_location(state):
        logger.debug("Getting %s location", entity_id)
        return _get_location_from_attributes(state)

    # Check if device is inside a zone.
    zone_state = opp.states.get(f"zone.{state.state}")
    if location.has_location(zone_state):
        logger.debug(
            "%s is in %s, getting zone location", entity_id, zone_state.entity_id
        )
        return _get_location_from_attributes(zone_state)

    # If zone was not found in state then use the state as the location.
    if entity_id.startswith("sensor."):
        return state.state

    # When everything fails just return nothing.
    return None


def resolve_zone(opp, friendly_name):
    """Get a lat/long from a zones friendly_name."""
    states = opp.states.all()
    for state in states:
        if state.domain == "zone" and state.name == friendly_name:
            return _get_location_from_attributes(state)

    return friendly_name


def _get_location_from_attributes(state):
    """Get the lat/long string from an states attributes."""
    attr = state.attributes
    return f"{attr.get(ATTR_LATITUDE)},{attr.get(ATTR_LONGITUDE)}"
