"""Test air_quality of Airly integration."""
from datetime import timedelta

from airly.exceptions import AirlyError

from openpeerpower.components.air_quality import ATTR_AQI, ATTR_PM_2_5, ATTR_PM_10
from openpeerpower.components.airly.air_quality import (
    ATTRIBUTION,
    LABEL_ADVICE,
    LABEL_AQI_DESCRIPTION,
    LABEL_AQI_LEVEL,
    LABEL_PM_2_5_LIMIT,
    LABEL_PM_2_5_PERCENT,
    LABEL_PM_10_LIMIT,
    LABEL_PM_10_PERCENT,
)
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_ENTITY_ID,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    HTTP_INTERNAL_SERVER_ERROR,
    STATE_UNAVAILABLE,
)
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from . import API_POINT_URL

from tests.common import async_fire_time_changed, load_fixture
from tests.components.airly import init_integration


async def test_air_quality.opp, aioclient_mock):
    """Test states of the air_quality."""
    await init_integration.opp, aioclient_mock)
    registry = await.opp.helpers.entity_registry.async_get_registry()

    state =.opp.states.get("air_quality.home")
    assert state
    assert state.state == "14"
    assert state.attributes.get(ATTR_AQI) == 23
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(LABEL_ADVICE) == "Great air!"
    assert state.attributes.get(ATTR_PM_10) == 19
    assert state.attributes.get(ATTR_PM_2_5) == 14
    assert state.attributes.get(LABEL_AQI_DESCRIPTION) == "Great air here today!"
    assert state.attributes.get(LABEL_AQI_LEVEL) == "very low"
    assert state.attributes.get(LABEL_PM_2_5_LIMIT) == 25.0
    assert state.attributes.get(LABEL_PM_2_5_PERCENT) == 55
    assert state.attributes.get(LABEL_PM_10_LIMIT) == 50.0
    assert state.attributes.get(LABEL_PM_10_PERCENT) == 37
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:blur"

    entry = registry.async_get("air_quality.home")
    assert entry
    assert entry.unique_id == "123-456"


async def test_availability.opp, aioclient_mock):
    """Ensure that we mark the entities unavailable correctly when service causes an error."""
    await init_integration.opp, aioclient_mock)

    state =.opp.states.get("air_quality.home")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "14"

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        API_POINT_URL, exc=AirlyError(HTTP_INTERNAL_SERVER_ERROR, "Unexpected error")
    )
    future = utcnow() + timedelta(minutes=60)

    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state =.opp.states.get("air_quality.home")
    assert state
    assert state.state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_POINT_URL, text=load_fixture("airly_valid_station.json"))
    future = utcnow() + timedelta(minutes=120)

    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state =.opp.states.get("air_quality.home")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "14"


async def test_manual_update_entity.opp, aioclient_mock):
    """Test manual update entity via service homeasasistant/update_entity."""
    await init_integration.opp, aioclient_mock)

    call_count = aioclient_mock.call_count
    await async_setup_component.opp, "openpeerpower", {})
    await.opp.services.async_call(
        "openpeerpower",
        "update_entity",
        {ATTR_ENTITY_ID: ["air_quality.home"]},
        blocking=True,
    )

    assert aioclient_mock.call_count == call_count + 1
