"""The tests for the demo platform."""

from unittest.mock import patch

import pytest

from openpeerpower.components import geo_location
from openpeerpower.components.demo.geo_location import (
    DEFAULT_UPDATE_INTERVAL,
    NUMBER_OF_DEMO_DEVICES,
)
from openpeerpower.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_UNIT_OF_MEASUREMENT,
    LENGTH_KILOMETERS,
)
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed

CONFIG = {geo_location.DOMAIN: [{"platform": "demo"}]}


@pytest.fixture(autouse=True)
def mock_legacy_time(legacy_patchable_time):
    """Make time patchable for all the tests."""
    yield


async def test_setup_platform.opp):
    """Test setup of demo platform via configuration."""
    utcnow = dt_util.utcnow()
    # Patching 'utcnow' to gain more control over the timed update.
    with patch("openpeerpower.util.dt.utcnow", return_value=utcnow):
        with assert_setup_component(1, geo_location.DOMAIN):
            assert await async_setup_component.opp, geo_location.DOMAIN, CONFIG)
        await opp.async_block_till_done()

        # In this test, one zone and geolocation entities have been
        # generated.
        all_states = [
            opp.states.get(entity_id)
            for entity_id in.opp.states.async_entity_ids(geo_location.DOMAIN)
        ]
        assert len(all_states) == NUMBER_OF_DEMO_DEVICES

        for state in all_states:
            # Check a single device's attributes.
            if state.domain != geo_location.DOMAIN:
                # ignore home zone state
                continue
            assert abs(state.attributes[ATTR_LATITUDE] -.opp.config.latitude) < 1.0
            assert abs(state.attributes[ATTR_LONGITUDE] -.opp.config.longitude) < 1.0
            assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == LENGTH_KILOMETERS

        # Update (replaces 1 device).
        async_fire_time_changed.opp, utcnow + DEFAULT_UPDATE_INTERVAL)
        await opp.async_block_till_done()
        # Get all states again, ensure that the number of states is still
        # the same, but the lists are different.
        all_states_updated = [
            opp.states.get(entity_id)
            for entity_id in.opp.states.async_entity_ids(geo_location.DOMAIN)
        ]
        assert len(all_states_updated) == NUMBER_OF_DEMO_DEVICES
        assert all_states != all_states_updated
