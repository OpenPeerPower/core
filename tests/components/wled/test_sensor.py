"""Tests for the WLED sensor platform."""
from datetime import datetime
from unittest.mock import patch

import pytest

from openpeerpower.components.sensor import (
    DEVICE_CLASS_CURRENT,
    DOMAIN as SENSOR_DOMAIN,
)
from openpeerpower.components.wled.const import (
    ATTR_LED_COUNT,
    ATTR_MAX_POWER,
    CURRENT_MA,
    DOMAIN,
)
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    DATA_BYTES,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.util import dt as dt_util

from tests.components.wled import init_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_sensors(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the creation and values of the WLED sensors."""

    entry = await init_integration.opp, aioclient_mock, skip_setup=True)
    registry = await.opp.helpers.entity_registry.async_get_registry()

    # Pre-create registry entries for disabled by default sensors
    registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "aabbccddeeff_uptime",
        suggested_object_id="wled_rgb_light_uptime",
        disabled_by=None,
    )

    registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "aabbccddeeff_free_heap",
        suggested_object_id="wled_rgb_light_free_memory",
        disabled_by=None,
    )

    registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "aabbccddeeff_wifi_signal",
        suggested_object_id="wled_rgb_light_wifi_signal",
        disabled_by=None,
    )

    registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "aabbccddeeff_wifi_rssi",
        suggested_object_id="wled_rgb_light_wifi_rssi",
        disabled_by=None,
    )

    registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "aabbccddeeff_wifi_channel",
        suggested_object_id="wled_rgb_light_wifi_channel",
        disabled_by=None,
    )

    registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "aabbccddeeff_wifi_bssid",
        suggested_object_id="wled_rgb_light_wifi_bssid",
        disabled_by=None,
    )

    # Setup
    test_time = datetime(2019, 11, 11, 9, 10, 32, tzinfo=dt_util.UTC)
    with patch("openpeerpower.components.wled.sensor.utcnow", return_value=test_time):
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    state = opp.states.get("sensor.wled_rgb_light_estimated_current")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:power"
    assert state.attributes.get(ATTR_LED_COUNT) == 30
    assert state.attributes.get(ATTR_MAX_POWER) == 850
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == CURRENT_MA
    assert state.attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_CURRENT
    assert state.state == "470"

    entry = registry.async_get("sensor.wled_rgb_light_estimated_current")
    assert entry
    assert entry.unique_id == "aabbccddeeff_estimated_current"

    state = opp.states.get("sensor.wled_rgb_light_uptime")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:clock-outline"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.state == "2019-11-11T09:10:00+00:00"

    entry = registry.async_get("sensor.wled_rgb_light_uptime")
    assert entry
    assert entry.unique_id == "aabbccddeeff_uptime"

    state = opp.states.get("sensor.wled_rgb_light_free_memory")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:memory"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == DATA_BYTES
    assert state.state == "14600"

    entry = registry.async_get("sensor.wled_rgb_light_free_memory")
    assert entry
    assert entry.unique_id == "aabbccddeeff_free_heap"

    state = opp.states.get("sensor.wled_rgb_light_wifi_signal")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:wifi"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE
    assert state.state == "76"

    entry = registry.async_get("sensor.wled_rgb_light_wifi_signal")
    assert entry
    assert entry.unique_id == "aabbccddeeff_wifi_signal"

    state = opp.states.get("sensor.wled_rgb_light_wifi_rssi")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:wifi"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )
    assert state.state == "-62"

    entry = registry.async_get("sensor.wled_rgb_light_wifi_rssi")
    assert entry
    assert entry.unique_id == "aabbccddeeff_wifi_rssi"

    state = opp.states.get("sensor.wled_rgb_light_wifi_channel")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:wifi"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.state == "11"

    entry = registry.async_get("sensor.wled_rgb_light_wifi_channel")
    assert entry
    assert entry.unique_id == "aabbccddeeff_wifi_channel"

    state = opp.states.get("sensor.wled_rgb_light_wifi_bssid")
    assert state
    assert state.attributes.get(ATTR_ICON) == "mdi:wifi"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.state == "AA:AA:AA:AA:AA:BB"

    entry = registry.async_get("sensor.wled_rgb_light_wifi_bssid")
    assert entry
    assert entry.unique_id == "aabbccddeeff_wifi_bssid"


@pytest.mark.parametrize(
    "entity_id",
    (
        "sensor.wled_rgb_light_uptime",
        "sensor.wled_rgb_light_free_memory",
        "sensor.wled_rgb_light_wi_fi_signal",
        "sensor.wled_rgb_light_wi_fi_rssi",
        "sensor.wled_rgb_light_wi_fi_channel",
        "sensor.wled_rgb_light_wi_fi_bssid",
    ),
)
async def test_disabled_by_default_sensors(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker, entity_id: str
) -> None:
    """Test the disabled by default WLED sensors."""
    await init_integration.opp, aioclient_mock)
    registry = await.opp.helpers.entity_registry.async_get_registry()

    state = opp.states.get(entity_id)
    assert state is None

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.disabled
    assert entry.disabled_by == "integration"
