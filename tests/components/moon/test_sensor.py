"""The test for the moon sensor platform."""
from datetime import datetime
from unittest.mock import patch

from openpeerpower.components.openpeerpower import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

DAY1 = datetime(2017, 1, 1, 1, tzinfo=dt_util.UTC)
DAY2 = datetime(2017, 1, 18, 1, tzinfo=dt_util.UTC)


async def test_moon_day1(opp):
    """Test the Moon sensor."""
    config = {"sensor": {"platform": "moon", "name": "moon_day1"}}

    await async_setup_component(opp, HA_DOMAIN, {})
    assert await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()

    assert opp.states.get("sensor.moon_day1")

    with patch(
        "openpeerpower.components.moon.sensor.dt_util.utcnow", return_value=DAY1
    ):
        await async_update_entity(opp, "sensor.moon_day1")

    assert opp.states.get("sensor.moon_day1").state == "waxing_crescent"


async def test_moon_day2(opp):
    """Test the Moon sensor."""
    config = {"sensor": {"platform": "moon", "name": "moon_day2"}}

    await async_setup_component(opp, HA_DOMAIN, {})
    assert await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()

    assert opp.states.get("sensor.moon_day2")

    with patch(
        "openpeerpower.components.moon.sensor.dt_util.utcnow", return_value=DAY2
    ):
        await async_update_entity(opp, "sensor.moon_day2")

    assert opp.states.get("sensor.moon_day2").state == "waning_gibbous"


async def async_update_entity(opp, entity_id):
    """Run an update action for an entity."""
    await opp.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await opp.async_block_till_done()
