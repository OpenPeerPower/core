"""The tests for the Sun helpers."""
# pylint: disable=protected-access
from datetime import datetime, timedelta
from unittest.mock import patch

from openpeerpower.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
import openpeerpower.helpers.sun as sun
import openpeerpower.util.dt as dt_util


def test_next_events(opp):
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    from astral import LocationInfo
    import astral.sun

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=opp.config.latitude, longitude=opp.config.longitude
    )

    mod = -1
    while True:
        next_dawn = astral.sun.dawn(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_dawn > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_dusk = astral.sun.dusk(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_dusk > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_midnight = astral.sun.midnight(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_midnight > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_noon = astral.sun.noon(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_noon > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_rising = astral.sun.sunrise(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_rising > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_setting = astral.sun.sunset(
            location.observer, utc_today + timedelta(days=mod)
        )
        if next_setting > utc_now:
            break
        mod += 1

    with patch("openpeerpower.helpers.condition.dt_util.utcnow", return_value=utc_now):
        assert next_dawn == sun.get_astral_event_next(opp, "dawn")
        assert next_dusk == sun.get_astral_event_next(opp, "dusk")
        assert next_midnight == sun.get_astral_event_next(opp, "midnight")
        assert next_noon == sun.get_astral_event_next(opp, "noon")
        assert next_rising == sun.get_astral_event_next(opp, SUN_EVENT_SUNRISE)
        assert next_setting == sun.get_astral_event_next(opp, SUN_EVENT_SUNSET)


def test_date_events(opp):
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    from astral import LocationInfo
    import astral.sun

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=opp.config.latitude, longitude=opp.config.longitude
    )

    dawn = astral.sun.dawn(location.observer, utc_today)
    dusk = astral.sun.dusk(location.observer, utc_today)
    midnight = astral.sun.midnight(location.observer, utc_today)
    noon = astral.sun.noon(location.observer, utc_today)
    sunrise = astral.sun.sunrise(location.observer, utc_today)
    sunset = astral.sun.sunset(location.observer, utc_today)

    assert dawn == sun.get_astral_event_date(opp, "dawn", utc_today)
    assert dusk == sun.get_astral_event_date(opp, "dusk", utc_today)
    assert midnight == sun.get_astral_event_date(opp, "midnight", utc_today)
    assert noon == sun.get_astral_event_date(opp, "noon", utc_today)
    assert sunrise == sun.get_astral_event_date(opp, SUN_EVENT_SUNRISE, utc_today)
    assert sunset == sun.get_astral_event_date(opp, SUN_EVENT_SUNSET, utc_today)


def test_date_events_default_date(opp):
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    from astral import LocationInfo
    import astral.sun

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=opp.config.latitude, longitude=opp.config.longitude
    )

    dawn = astral.sun.dawn(location.observer, date=utc_today)
    dusk = astral.sun.dusk(location.observer, date=utc_today)
    midnight = astral.sun.midnight(location.observer, date=utc_today)
    noon = astral.sun.noon(location.observer, date=utc_today)
    sunrise = astral.sun.sunrise(location.observer, date=utc_today)
    sunset = astral.sun.sunset(location.observer, date=utc_today)

    with patch("openpeerpower.util.dt.now", return_value=utc_now):
        assert dawn == sun.get_astral_event_date(opp, "dawn", utc_today)
        assert dusk == sun.get_astral_event_date(opp, "dusk", utc_today)
        assert midnight == sun.get_astral_event_date(opp, "midnight", utc_today)
        assert noon == sun.get_astral_event_date(opp, "noon", utc_today)
        assert sunrise == sun.get_astral_event_date(opp, SUN_EVENT_SUNRISE, utc_today)
        assert sunset == sun.get_astral_event_date(opp, SUN_EVENT_SUNSET, utc_today)


def test_date_events_accepts_datetime(opp):
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    from astral import LocationInfo
    import astral.sun

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=opp.config.latitude, longitude=opp.config.longitude
    )

    dawn = astral.sun.dawn(location.observer, date=utc_today)
    dusk = astral.sun.dusk(location.observer, date=utc_today)
    midnight = astral.sun.midnight(location.observer, date=utc_today)
    noon = astral.sun.noon(location.observer, date=utc_today)
    sunrise = astral.sun.sunrise(location.observer, date=utc_today)
    sunset = astral.sun.sunset(location.observer, date=utc_today)

    assert dawn == sun.get_astral_event_date(opp, "dawn", utc_now)
    assert dusk == sun.get_astral_event_date(opp, "dusk", utc_now)
    assert midnight == sun.get_astral_event_date(opp, "midnight", utc_now)
    assert noon == sun.get_astral_event_date(opp, "noon", utc_now)
    assert sunrise == sun.get_astral_event_date(opp, SUN_EVENT_SUNRISE, utc_now)
    assert sunset == sun.get_astral_event_date(opp, SUN_EVENT_SUNSET, utc_now)


def test_is_up(opp):
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 12, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.helpers.condition.dt_util.utcnow", return_value=utc_now):
        assert not sun.is_up(opp)

    utc_now = datetime(2016, 11, 1, 18, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpower.helpers.condition.dt_util.utcnow", return_value=utc_now):
        assert sun.is_up(opp)


def test_norway_in_june(opp):
    """Test location in Norway where the sun doesn't set in summer."""
    opp.config.latitude = 69.6
    opp.config.longitude = 18.8

    june = datetime(2016, 6, 1, tzinfo=dt_util.UTC)

    print(sun.get_astral_event_date(opp, SUN_EVENT_SUNRISE, datetime(2017, 7, 25)))
    print(sun.get_astral_event_date(opp, SUN_EVENT_SUNSET, datetime(2017, 7, 25)))

    print(sun.get_astral_event_date(opp, SUN_EVENT_SUNRISE, datetime(2017, 7, 26)))
    print(sun.get_astral_event_date(opp, SUN_EVENT_SUNSET, datetime(2017, 7, 26)))

    assert sun.get_astral_event_next(opp, SUN_EVENT_SUNRISE, june) == datetime(
        2016, 7, 24, 22, 59, 45, 689645, tzinfo=dt_util.UTC
    )
    assert sun.get_astral_event_next(opp, SUN_EVENT_SUNSET, june) == datetime(
        2016, 7, 25, 22, 17, 13, 503932, tzinfo=dt_util.UTC
    )
    assert sun.get_astral_event_date(opp, SUN_EVENT_SUNRISE, june) is None
    assert sun.get_astral_event_date(opp, SUN_EVENT_SUNSET, june) is None
