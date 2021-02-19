"""The tests for the Sun component."""
from datetime import datetime, timedelta
from unittest.mock import patch

from pytest import mark

import openpeerpower.components.sun as sun
from openpeerpower.const import EVENT_STATE_CHANGED
import openpeerpowerr.core as ha
from openpeerpowerr.setup import async_setup_component
import openpeerpowerr.util.dt as dt_util


async def test_setting_rising.opp, legacy_patchable_time):
    """Test retrieving sun setting and rising."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(
           .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
        )

    await.opp.async_block_till_done()
    state =.opp.states.get(sun.ENTITY_ID)

    from astral import Astral

    astral = Astral()
    utc_today = utc_now.date()

    latitude =.opp.config.latitude
    longitude =.opp.config.longitude

    mod = -1
    while True:
        next_dawn = astral.dawn_utc(
            utc_today + timedelta(days=mod), latitude, longitude
        )
        if next_dawn > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_dusk = astral.dusk_utc(
            utc_today + timedelta(days=mod), latitude, longitude
        )
        if next_dusk > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_midnight = astral.solar_midnight_utc(
            utc_today + timedelta(days=mod), longitude
        )
        if next_midnight > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_noon = astral.solar_noon_utc(utc_today + timedelta(days=mod), longitude)
        if next_noon > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_rising = astral.sunrise_utc(
            utc_today + timedelta(days=mod), latitude, longitude
        )
        if next_rising > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_setting = astral.sunset_utc(
            utc_today + timedelta(days=mod), latitude, longitude
        )
        if next_setting > utc_now:
            break
        mod += 1

    assert next_dawn == dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_DAWN]
    )
    assert next_dusk == dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_DUSK]
    )
    assert next_midnight == dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_MIDNIGHT]
    )
    assert next_noon == dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_NOON]
    )
    assert next_rising == dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_RISING]
    )
    assert next_setting == dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_SETTING]
    )


async def test_state_change.opp, legacy_patchable_time):
    """Test if the state changes at next setting/rising."""
    now = datetime(2016, 6, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    with patch("openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=now):
        await async_setup_component(
           .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
        )

    await.opp.async_block_till_done()

    test_time = dt_util.parse_datetime(
       .opp.states.get(sun.ENTITY_ID).attributes[sun.STATE_ATTR_NEXT_RISING]
    )
    assert test_time is not None

    assert sun.STATE_BELOW_HORIZON ==.opp.states.get(sun.ENTITY_ID).state

    patched_time = test_time + timedelta(seconds=5)
    with patch(
        "openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=patched_time
    ):
       .opp.bus.async_fire(op.EVENT_TIME_CHANGED, {op.ATTR_NOW: patched_time})
        await.opp.async_block_till_done()

    assert sun.STATE_ABOVE_HORIZON ==.opp.states.get(sun.ENTITY_ID).state

    with patch("openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=now):
        await.opp.config.async_update(longitude.opp.config.longitude + 90)
        await.opp.async_block_till_done()

    assert sun.STATE_ABOVE_HORIZON ==.opp.states.get(sun.ENTITY_ID).state


async def test_norway_in_june.opp):
    """Test location in Norway where the sun doesn't set in summer."""
   .opp.config.latitude = 69.6
   .opp.config.longitude = 18.8

    june = datetime(2016, 6, 1, tzinfo=dt_util.UTC)

    with patch("openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=june):
        assert await async_setup_component(
           .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
        )

    state =.opp.states.get(sun.ENTITY_ID)
    assert state is not None

    assert dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_RISING]
    ) == datetime(2016, 7, 25, 23, 23, 39, tzinfo=dt_util.UTC)
    assert dt_util.parse_datetime(
        state.attributes[sun.STATE_ATTR_NEXT_SETTING]
    ) == datetime(2016, 7, 26, 22, 19, 1, tzinfo=dt_util.UTC)

    assert state.state == sun.STATE_ABOVE_HORIZON


@mark.skip
async def test_state_change_count.opp):
    """Count the number of state change events in a location."""
    # Skipped because it's a bit slow. Has been validated with
    # multiple lattitudes and dates
   .opp.config.latitude = 10
   .opp.config.longitude = 0

    now = datetime(2016, 6, 1, tzinfo=dt_util.UTC)

    with patch("openpeerpowerr.helpers.condition.dt_util.utcnow", return_value=now):
        assert await async_setup_component(
           .opp, sun.DOMAIN, {sun.DOMAIN: {sun.CONF_ELEVATION: 0}}
        )

    events = []

    @op.callback
    def state_change_listener(event):
        if event.data.get("entity_id") == "sun.sun":
            events.append(event)

   .opp.bus.async_listen(EVENT_STATE_CHANGED, state_change_listener)
    await.opp.async_block_till_done()

    for _ in range(24 * 60 * 60):
        now += timedelta(seconds=1)
       .opp.bus.async_fire(op.EVENT_TIME_CHANGED, {op.ATTR_NOW: now})
        await.opp.async_block_till_done()

    assert len(events) < 721
