"""Tests for the Atag water heater platform."""
from unittest.mock import patch

from openpeerpower.components.atag import DOMAIN, WATER_HEATER
from openpeerpower.components.water_heater import SERVICE_SET_TEMPERATURE
from openpeerpower.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import entity_registry as er

from tests.components.atag import UID, init_integration
from tests.test_util.aiohttp import AiohttpClientMocker

WATER_HEATER_ID = f"{WATER_HEATER}.{DOMAIN}"


async def test_water_heater(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the creation of Atag water heater."""
    with patch("pyatag.entities.DHW.status"):
        entry = await init_integration(opp, aioclient_mock)
        registry = er.async_get(opp)

        assert registry.async_is_registered(WATER_HEATER_ID)
        entry = registry.async_get(WATER_HEATER_ID)
        assert entry.unique_id == f"{UID}-{WATER_HEATER}"


async def test_setting_target_temperature(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test setting the water heater device."""
    await init_integration(opp, aioclient_mock)
    with patch("pyatag.entities.DHW.set_temp") as mock_set_temp:
        await opp.services.async_call(
            WATER_HEATER,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: WATER_HEATER_ID, ATTR_TEMPERATURE: 50},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_set_temp.assert_called_once_with(50)
