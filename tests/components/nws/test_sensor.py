"""Sensors for National Weather Service (NWS)."""
import pytest

from openpeerpower.components.nws.const import (
    ATTR_LABEL,
    ATTRIBUTION,
    DOMAIN,
    SENSOR_TYPES,
)
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import ATTR_ATTRIBUTION, STATE_UNKNOWN
from openpeerpower.util import slugify
from openpeerpower.util.unit_system import IMPERIAL_SYSTEM, METRIC_SYSTEM

from tests.common import MockConfigEntry
from tests.components.nws.const import (
    EXPECTED_FORECAST_IMPERIAL,
    EXPECTED_FORECAST_METRIC,
    NONE_OBSERVATION,
    NWS_CONFIG,
    SENSOR_EXPECTED_OBSERVATION_IMPERIAL,
    SENSOR_EXPECTED_OBSERVATION_METRIC,
)


@pytest.mark.parametrize(
    "units,result_observation,result_forecast",
    [
        (
            IMPERIAL_SYSTEM,
            SENSOR_EXPECTED_OBSERVATION_IMPERIAL,
            EXPECTED_FORECAST_IMPERIAL,
        ),
        (METRIC_SYSTEM, SENSOR_EXPECTED_OBSERVATION_METRIC, EXPECTED_FORECAST_METRIC),
    ],
)
async def test_imperial_metric(
    opp, units, result_observation, result_forecast, mock_simple_nws, no_weather
):
    """Test with imperial and metric units."""
    registry = await opp.helpers.entity_registry.async_get_registry()

    for sensor_name, sensor_data in SENSOR_TYPES.items():
        registry.async_get_or_create(
            SENSOR_DOMAIN,
            DOMAIN,
            f"35_-75_{sensor_name}",
            suggested_object_id=f"abc_{sensor_data[ATTR_LABEL]}",
            disabled_by=None,
        )

    opp.config.units = units
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=NWS_CONFIG,
    )
    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    for sensor_name, sensor_data in SENSOR_TYPES.items():
        state = opp.states.get(f"sensor.abc_{slugify(sensor_data[ATTR_LABEL])}")
        assert state
        assert state.state == result_observation[sensor_name]
        assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION


async def test_none_values(opp, mock_simple_nws, no_weather):
    """Test with no values."""
    instance = mock_simple_nws.return_value
    instance.observation = NONE_OBSERVATION

    registry = await opp.helpers.entity_registry.async_get_registry()

    for sensor_name, sensor_data in SENSOR_TYPES.items():
        registry.async_get_or_create(
            SENSOR_DOMAIN,
            DOMAIN,
            f"35_-75_{sensor_name}",
            suggested_object_id=f"abc_{sensor_data[ATTR_LABEL]}",
            disabled_by=None,
        )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=NWS_CONFIG,
    )
    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    for sensor_name, sensor_data in SENSOR_TYPES.items():
        state = opp.states.get(f"sensor.abc_{slugify(sensor_data[ATTR_LABEL])}")
        assert state
        assert state.state == STATE_UNKNOWN
