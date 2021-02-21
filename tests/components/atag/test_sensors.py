"""Tests for the Atag sensor platform."""

from openpeerpower.components.atag.sensor import SENSORS
from openpeerpower.core import OpenPeerPower

from tests.components.atag import UID, init_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_sensors(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the creation of ATAG sensors."""
    entry = await init_integration.opp, aioclient_mock)
    registry = await.opp.helpers.entity_registry.async_get_registry()

    for item in SENSORS:
        sensor_id = "_".join(f"sensor.{item}".lower().split())
        assert registry.async_is_registered(sensor_id)
        entry = registry.async_get(sensor_id)
        assert entry.unique_id in [f"{UID}-{v}" for v in SENSORS.values()]
