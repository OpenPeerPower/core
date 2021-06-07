"""Test air_quality of GIOS integration."""
from datetime import timedelta
import json
from unittest.mock import patch

from gios import ApiError

from openpeerpower.components.air_quality import (
    ATTR_AQI,
    ATTR_CO,
    ATTR_NO2,
    ATTR_OZONE,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SO2,
    DOMAIN as AIR_QUALITY_DOMAIN,
)
from openpeerpower.components.gios.air_quality import ATTRIBUTION
from openpeerpower.components.gios.const import AQI_GOOD, DOMAIN
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    STATE_UNAVAILABLE,
)
from openpeerpower.helpers import entity_registry as er
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed, load_fixture
from tests.components.gios import init_integration


async def test_air_quality(opp):
    """Test states of the air_quality."""
    await init_integration(opp)
    registry = er.async_get(opp)

    state = opp.states.get("air_quality.home")
    assert state
    assert state.state == "4"
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_AQI) == AQI_GOOD
    assert state.attributes.get(ATTR_PM_10) == 17
    assert state.attributes.get(ATTR_PM_2_5) == 4
    assert state.attributes.get(ATTR_CO) == 252
    assert state.attributes.get(ATTR_SO2) == 4
    assert state.attributes.get(ATTR_NO2) == 7
    assert state.attributes.get(ATTR_OZONE) == 96
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:emoticon-happy"
    assert state.attributes.get("station") == "Test Name 1"

    entry = registry.async_get("air_quality.home")
    assert entry
    assert entry.unique_id == "123"


async def test_air_quality_with_incomplete_data(opp):
    """Test states of the air_quality with incomplete data from measuring station."""
    await init_integration(opp, incomplete_data=True)
    registry = er.async_get(opp)

    state = opp.states.get("air_quality.home")
    assert state
    assert state.state == "4"
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_AQI) == "foo"
    assert state.attributes.get(ATTR_PM_10) is None
    assert state.attributes.get(ATTR_PM_2_5) == 4
    assert state.attributes.get(ATTR_CO) == 252
    assert state.attributes.get(ATTR_SO2) == 4
    assert state.attributes.get(ATTR_NO2) == 7
    assert state.attributes.get(ATTR_OZONE) == 96
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:blur"
    assert state.attributes.get("station") == "Test Name 1"

    entry = registry.async_get("air_quality.home")
    assert entry
    assert entry.unique_id == "123"


async def test_availability(opp):
    """Ensure that we mark the entities unavailable correctly when service causes an error."""
    await init_integration(opp)

    state = opp.states.get("air_quality.home")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "4"

    future = utcnow() + timedelta(minutes=60)
    with patch(
        "openpeerpower.components.gios.Gios._get_all_sensors",
        side_effect=ApiError("Unexpected error"),
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        state = opp.states.get("air_quality.home")
        assert state
        assert state.state == STATE_UNAVAILABLE

    future = utcnow() + timedelta(minutes=120)
    with patch(
        "openpeerpower.components.gios.Gios._get_all_sensors",
        return_value=json.loads(load_fixture("gios/sensors.json")),
    ), patch(
        "openpeerpower.components.gios.Gios._get_indexes",
        return_value=json.loads(load_fixture("gios/indexes.json")),
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        state = opp.states.get("air_quality.home")
        assert state
        assert state.state != STATE_UNAVAILABLE
        assert state.state == "4"


async def test_migrate_unique_id(opp):
    """Test migrate unique_id of the air_quality entity."""
    registry = er.async_get(opp)

    # Pre-create registry entries for disabled by default sensors
    registry.async_get_or_create(
        AIR_QUALITY_DOMAIN,
        DOMAIN,
        123,
        suggested_object_id="home",
        disabled_by=None,
    )

    await init_integration(opp)

    entry = registry.async_get("air_quality.home")
    assert entry
    assert entry.unique_id == "123"
