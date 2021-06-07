"""Helpers for Google Time Travel integration."""
from googlemaps import Client
from googlemaps.distance_matrix import distance_matrix
from googlemaps.exceptions import ApiError

from openpeerpower.components.google_travel_time.const import TRACKABLE_DOMAINS
from openpeerpower.const import ATTR_LATITUDE, ATTR_LONGITUDE
from openpeerpower.helpers import location


def is_valid_config_entry(opp, logger, api_key, origin, destination):
    """Return whether the config entry data is valid."""
    origin = resolve_location(opp, logger, origin)
    destination = resolve_location(opp, logger, destination)
    client = Client(api_key, timeout=10)
    try:
        distance_matrix(client, origin, destination, mode="driving")
    except ApiError:
        return False
    return True


def resolve_location(opp, logger, loc):
    """Resolve a location."""
    if loc.split(".", 1)[0] in TRACKABLE_DOMAINS:
        return get_location_from_entity(opp, logger, loc)

    return resolve_zone(opp, loc)


def get_location_from_entity(opp, logger, entity_id):
    """Get the location from the entity state or attributes."""
    entity = opp.states.get(entity_id)

    if entity is None:
        logger.error("Unable to find entity %s", entity_id)
        return None

    # Check if the entity has location attributes
    if location.has_location(entity):
        return get_location_from_attributes(entity)

    # Check if device is in a zone
    zone_entity = opp.states.get("zone.%s" % entity.state)
    if location.has_location(zone_entity):
        logger.debug(
            "%s is in %s, getting zone location", entity_id, zone_entity.entity_id
        )
        return get_location_from_attributes(zone_entity)

    # If zone was not found in state then use the state as the location
    if entity_id.startswith("sensor."):
        return entity.state

    # When everything fails just return nothing
    return None


def get_location_from_attributes(entity):
    """Get the lat/long string from an entities attributes."""
    attr = entity.attributes
    return f"{attr.get(ATTR_LATITUDE)},{attr.get(ATTR_LONGITUDE)}"


def resolve_zone(opp, friendly_name):
    """Resolve a location from a zone's friendly name."""
    entities = opp.states.all()
    for entity in entities:
        if entity.domain == "zone" and entity.name == friendly_name:
            return get_location_from_attributes(entity)

    return friendly_name
