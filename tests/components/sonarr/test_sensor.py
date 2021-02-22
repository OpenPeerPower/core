"""Tests for the Sonarr sensor platform."""
from datetime import timedelta
from unittest.mock import patch

import pytest

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.components.sonarr.const import DOMAIN
from openpeerpower.const import (
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    DATA_GIGABYTES,
    STATE_UNAVAILABLE,
)
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.sonarr import mock_connection, setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker

UPCOMING_ENTITY_ID = f"{SENSOR_DOMAIN}.sonarr_upcoming"


async def test_sensors(
    opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the creation and values of the sensors."""
    entry = await setup_integration.opp, aioclient_mock, skip_entry_setup=True)
    registry = await.opp.helpers.entity_registry.async_get_registry()

    # Pre-create registry entries for disabled by default sensors
    sensors = {
        "commands": "sonarr_commands",
        "diskspace": "sonarr_disk_space",
        "queue": "sonarr_queue",
        "series": "sonarr_shows",
        "wanted": "sonarr_wanted",
    }

    for (unique, oid) in sensors.items():
        registry.async_get_or_create(
            SENSOR_DOMAIN,
            DOMAIN,
            f"{entry.entry_id}_{unique}",
            suggested_object_id=oid,
            disabled_by=None,
        )

    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    for (unique, oid) in sensors.items():
        entity = registry.async_get(f"sensor.{oid}")
        assert entity
        assert entity.unique_id == f"{entry.entry_id}_{unique}"

    state = opp.states.get("sensor.sonarr_commands")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:code-braces"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "Commands"
    assert state.state == "2"

    state = opp.states.get("sensor.sonarr_disk_space")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:harddisk"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == DATA_GIGABYTES
    assert state.state == "263.10"

    state = opp.states.get("sensor.sonarr_queue")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:download"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "Episodes"
    assert state.state == "1"

    state = opp.states.get("sensor.sonarr_shows")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:television"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "Series"
    assert state.state == "1"

    state = opp.states.get("sensor.sonarr_upcoming")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:television"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "Episodes"
    assert state.state == "1"

    state = opp.states.get("sensor.sonarr_wanted")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:television"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "Episodes"
    assert state.state == "2"


@pytest.mark.parametrize(
    "entity_id",
    (
        "sensor.sonarr_commands",
        "sensor.sonarr_disk_space",
        "sensor.sonarr_queue",
        "sensor.sonarr_shows",
        "sensor.sonarr_wanted",
    ),
)
async def test_disabled_by_default_sensors(
    opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker, entity_id: str
) -> None:
    """Test the disabled by default sensors."""
    await setup_integration.opp, aioclient_mock)
    registry = await.opp.helpers.entity_registry.async_get_registry()
    print(registry.entities)

    state = opp.states.get(entity_id)
    assert state is None

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.disabled
    assert entry.disabled_by == "integration"


async def test_availability(
    opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test entity availability."""
    now = dt_util.utcnow()

    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        await setup_integration.opp, aioclient_mock)

    assert.opp.states.get(UPCOMING_ENTITY_ID).state == "1"

    # state to unavailable
    aioclient_mock.clear_requests()
    mock_connection(aioclient_mock, error=True)

    future = now + timedelta(minutes=1)
    with patch("openpeerpower.util.dt.utcnow", return_value=future):
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    assert.opp.states.get(UPCOMING_ENTITY_ID).state == STATE_UNAVAILABLE

    # state to available
    aioclient_mock.clear_requests()
    mock_connection(aioclient_mock)

    future += timedelta(minutes=1)
    with patch("openpeerpower.util.dt.utcnow", return_value=future):
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    assert.opp.states.get(UPCOMING_ENTITY_ID).state == "1"

    # state to unavailable
    aioclient_mock.clear_requests()
    mock_connection(aioclient_mock, invalid_auth=True)

    future += timedelta(minutes=1)
    with patch("openpeerpower.util.dt.utcnow", return_value=future):
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    assert.opp.states.get(UPCOMING_ENTITY_ID).state == STATE_UNAVAILABLE

    # state to available
    aioclient_mock.clear_requests()
    mock_connection(aioclient_mock)

    future += timedelta(minutes=1)
    with patch("openpeerpower.util.dt.utcnow", return_value=future):
        async_fire_time_changed.opp, future)
        await.opp.async_block_till_done()

    assert.opp.states.get(UPCOMING_ENTITY_ID).state == "1"
