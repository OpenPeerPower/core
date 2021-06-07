"""Helpers for sun events."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from openpeerpower.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.loader import bind_opp
from openpeerpower.util import dt as dt_util

if TYPE_CHECKING:
    import astral

DATA_LOCATION_CACHE = "astral_location_cache"

ELEVATION_AGNOSTIC_EVENTS = ("noon", "midnight")


@callback
@bind_opp
def get_astral_location(
    opp: OpenPeerPower,
) -> tuple[astral.location.Location, astral.Elevation]:
    """Get an astral location for the current Open Peer Power configuration."""
    from astral import LocationInfo  # pylint: disable=import-outside-toplevel
    from astral.location import Location  # pylint: disable=import-outside-toplevel

    latitude = opp.config.latitude
    longitude = opp.config.longitude
    timezone = str(opp.config.time_zone)
    elevation = opp.config.elevation
    info = ("", "", timezone, latitude, longitude)

    # Cache astral locations so they aren't recreated with the same args
    if DATA_LOCATION_CACHE not in opp.data:
        opp.data[DATA_LOCATION_CACHE] = {}

    if info not in opp.data[DATA_LOCATION_CACHE]:
        opp.data[DATA_LOCATION_CACHE][info] = Location(LocationInfo(*info))

    return opp.data[DATA_LOCATION_CACHE][info], elevation


@callback
@bind_opp
def get_astral_event_next(
    opp: OpenPeerPower,
    event: str,
    utc_point_in_time: datetime.datetime | None = None,
    offset: datetime.timedelta | None = None,
) -> datetime.datetime:
    """Calculate the next specified solar event."""
    location, elevation = get_astral_location(opp)
    return get_location_astral_event_next(
        location, elevation, event, utc_point_in_time, offset
    )


@callback
def get_location_astral_event_next(
    location: astral.location.Location,
    elevation: astral.Elevation,
    event: str,
    utc_point_in_time: datetime.datetime | None = None,
    offset: datetime.timedelta | None = None,
) -> datetime.datetime:
    """Calculate the next specified solar event."""

    if offset is None:
        offset = datetime.timedelta()

    if utc_point_in_time is None:
        utc_point_in_time = dt_util.utcnow()

    kwargs = {"local": False}
    if event not in ELEVATION_AGNOSTIC_EVENTS:
        kwargs["observer_elevation"] = elevation

    mod = -1
    while True:
        try:
            next_dt: datetime.datetime = (
                getattr(location, event)(
                    dt_util.as_local(utc_point_in_time).date()
                    + datetime.timedelta(days=mod),
                    **kwargs,
                )
                + offset
            )
            if next_dt > utc_point_in_time:
                return next_dt
        except ValueError:
            pass
        mod += 1


@callback
@bind_opp
def get_astral_event_date(
    opp: OpenPeerPower,
    event: str,
    date: datetime.date | datetime.datetime | None = None,
) -> datetime.datetime | None:
    """Calculate the astral event time for the specified date."""
    location, elevation = get_astral_location(opp)

    if date is None:
        date = dt_util.now().date()

    if isinstance(date, datetime.datetime):
        date = dt_util.as_local(date).date()

    kwargs = {"local": False}
    if event not in ELEVATION_AGNOSTIC_EVENTS:
        kwargs["observer_elevation"] = elevation

    try:
        return getattr(location, event)(date, **kwargs)  # type: ignore
    except ValueError:
        # Event never occurs for specified date.
        return None


@callback
@bind_opp
def is_up(
    opp: OpenPeerPower, utc_point_in_time: datetime.datetime | None = None
) -> bool:
    """Calculate if the sun is currently up."""
    if utc_point_in_time is None:
        utc_point_in_time = dt_util.utcnow()

    next_sunrise = get_astral_event_next(opp, SUN_EVENT_SUNRISE, utc_point_in_time)
    next_sunset = get_astral_event_next(opp, SUN_EVENT_SUNSET, utc_point_in_time)

    return next_sunrise > next_sunset
