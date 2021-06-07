"""Test the Advantage Air Binary Sensor Platform."""
from datetime import timedelta

from openpeerpower.config_entries import RELOAD_AFTER_UPDATE_DELAY
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.helpers import entity_registry as er
from openpeerpower.util import dt

from tests.common import async_fire_time_changed
from tests.components.advantage_air import (
    TEST_SET_RESPONSE,
    TEST_SET_URL,
    TEST_SYSTEM_DATA,
    TEST_SYSTEM_URL,
    add_mock_config,
)


async def test_binary_sensor_async_setup_entry(opp, aioclient_mock):
    """Test binary sensor setup."""

    aioclient_mock.get(
        TEST_SYSTEM_URL,
        text=TEST_SYSTEM_DATA,
    )
    aioclient_mock.get(
        TEST_SET_URL,
        text=TEST_SET_RESPONSE,
    )
    await add_mock_config(opp)

    registry = er.async_get(opp)

    assert len(aioclient_mock.mock_calls) == 1

    # Test First Air Filter
    entity_id = "binary_sensor.ac_one_filter"
    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-filter"

    # Test Second Air Filter
    entity_id = "binary_sensor.ac_two_filter"
    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ON

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac2-filter"

    # Test First Motion Sensor
    entity_id = "binary_sensor.zone_open_with_sensor_motion"
    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ON

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z01-motion"

    # Test Second Motion Sensor
    entity_id = "binary_sensor.zone_closed_with_sensor_motion"
    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z02-motion"

    # Test First MyZone Sensor (disabled by default)
    entity_id = "binary_sensor.zone_open_with_sensor_myzone"

    assert not opp.states.get(entity_id)

    registry.async_update_entity(entity_id=entity_id, disabled_by=None)
    await opp.async_block_till_done()

    async_fire_time_changed(
        opp,
        dt.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_ON

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z01-myzone"

    # Test Second Motion Sensor (disabled by default)
    entity_id = "binary_sensor.zone_closed_with_sensor_myzone"

    assert not opp.states.get(entity_id)

    registry.async_update_entity(entity_id=entity_id, disabled_by=None)
    await opp.async_block_till_done()

    async_fire_time_changed(
        opp,
        dt.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z02-myzone"
