"""Tests for Climacell sensor entities."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from unittest.mock import patch

import pytest

from openpeerpower.components.climacell.config_flow import (
    _get_config_schema,
    _get_unique_id,
)
from openpeerpower.components.climacell.const import ATTRIBUTION, DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import ATTR_ATTRIBUTION
from openpeerpower.core import OpenPeerPower, State, callback
from openpeerpower.helpers.entity_registry import async_get
from openpeerpower.util import dt as dt_util

from .const import API_V3_ENTRY_DATA, API_V4_ENTRY_DATA

from tests.common import MockConfigEntry

_LOGGER = logging.getLogger(__name__)
CC_SENSOR_ENTITY_ID = "sensor.climacell_{}"

CO = "carbon_monoxide"
NO2 = "nitrogen_dioxide"
SO2 = "sulfur_dioxide"
PM25 = "particulate_matter_2_5_mm"
PM10 = "particulate_matter_10_mm"
MEP_AQI = "china_mep_air_quality_index"
MEP_HEALTH_CONCERN = "china_mep_health_concern"
MEP_PRIMARY_POLLUTANT = "china_mep_primary_pollutant"
EPA_AQI = "us_epa_air_quality_index"
EPA_HEALTH_CONCERN = "us_epa_health_concern"
EPA_PRIMARY_POLLUTANT = "us_epa_primary_pollutant"
FIRE_INDEX = "fire_index"
GRASS_POLLEN = "grass_pollen_index"
WEED_POLLEN = "weed_pollen_index"
TREE_POLLEN = "tree_pollen_index"


@callback
def _enable_entity(opp: OpenPeerPower, entity_name: str) -> None:
    """Enable disabled entity."""
    ent_reg = async_get(opp)
    entry = ent_reg.async_get(entity_name)
    updated_entry = ent_reg.async_update_entity(
        entry.entity_id, **{"disabled_by": None}
    )
    assert updated_entry != entry
    assert updated_entry.disabled is False


async def _setup(opp: OpenPeerPower, config: dict[str, Any]) -> State:
    """Set up entry and return entity state."""
    with patch(
        "openpeerpower.util.dt.utcnow",
        return_value=datetime(2021, 3, 6, 23, 59, 59, tzinfo=dt_util.UTC),
    ):
        data = _get_config_schema(opp)(config)
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            unique_id=_get_unique_id(opp, data),
            version=1,
        )
        config_entry.add_to_opp(opp)
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        for entity_name in (
            CO,
            NO2,
            SO2,
            PM25,
            PM10,
            MEP_AQI,
            MEP_HEALTH_CONCERN,
            MEP_PRIMARY_POLLUTANT,
            EPA_AQI,
            EPA_HEALTH_CONCERN,
            EPA_PRIMARY_POLLUTANT,
            FIRE_INDEX,
            GRASS_POLLEN,
            WEED_POLLEN,
            TREE_POLLEN,
        ):
            _enable_entity(opp, CC_SENSOR_ENTITY_ID.format(entity_name))
        await opp.async_block_till_done()
        assert len(opp.states.async_entity_ids(SENSOR_DOMAIN)) == 15


def check_sensor_state(opp: OpenPeerPower, entity_name: str, value: str):
    """Check the state of a ClimaCell sensor."""
    state = opp.states.get(CC_SENSOR_ENTITY_ID.format(entity_name))
    assert state
    assert state.state == value
    assert state.attributes[ATTR_ATTRIBUTION] == ATTRIBUTION


async def test_v3_sensor(
    opp: OpenPeerPower,
    climacell_config_entry_update: pytest.fixture,
) -> None:
    """Test v3 sensor data."""
    await _setup(opp, API_V3_ENTRY_DATA)
    check_sensor_state(opp, CO, "0.875")
    check_sensor_state(opp, NO2, "14.1875")
    check_sensor_state(opp, SO2, "2")
    check_sensor_state(opp, PM25, "5.3125")
    check_sensor_state(opp, PM10, "27")
    check_sensor_state(opp, MEP_AQI, "27")
    check_sensor_state(opp, MEP_HEALTH_CONCERN, "Good")
    check_sensor_state(opp, MEP_PRIMARY_POLLUTANT, "pm10")
    check_sensor_state(opp, EPA_AQI, "22.3125")
    check_sensor_state(opp, EPA_HEALTH_CONCERN, "Good")
    check_sensor_state(opp, EPA_PRIMARY_POLLUTANT, "pm25")
    check_sensor_state(opp, FIRE_INDEX, "9")
    check_sensor_state(opp, GRASS_POLLEN, "minimal_to_none")
    check_sensor_state(opp, WEED_POLLEN, "minimal_to_none")
    check_sensor_state(opp, TREE_POLLEN, "minimal_to_none")


async def test_v4_sensor(
    opp: OpenPeerPower,
    climacell_config_entry_update: pytest.fixture,
) -> None:
    """Test v4 sensor data."""
    await _setup(opp, API_V4_ENTRY_DATA)
    check_sensor_state(opp, CO, "0.63")
    check_sensor_state(opp, NO2, "10.67")
    check_sensor_state(opp, SO2, "1.65")
    check_sensor_state(opp, PM25, "5.2972")
    check_sensor_state(opp, PM10, "20.1294")
    check_sensor_state(opp, MEP_AQI, "23")
    check_sensor_state(opp, MEP_HEALTH_CONCERN, "good")
    check_sensor_state(opp, MEP_PRIMARY_POLLUTANT, "pm10")
    check_sensor_state(opp, EPA_AQI, "24")
    check_sensor_state(opp, EPA_HEALTH_CONCERN, "good")
    check_sensor_state(opp, EPA_PRIMARY_POLLUTANT, "pm25")
    check_sensor_state(opp, FIRE_INDEX, "10")
    check_sensor_state(opp, GRASS_POLLEN, "none")
    check_sensor_state(opp, WEED_POLLEN, "none")
    check_sensor_state(opp, TREE_POLLEN, "none")
