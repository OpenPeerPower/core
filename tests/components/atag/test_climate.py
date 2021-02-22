"""Tests for the Atag climate platform."""

from unittest.mock import PropertyMock, patch

from openpeerpower.components.atag import CLIMATE, DOMAIN
from openpeerpower.components.climate import (
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_HEAT,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
)
from openpeerpower.components.climate.const import CURRENT_HVAC_HEAT, PRESET_AWAY
from openpeerpower.components.openpeerpower import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from openpeerpower.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, STATE_UNKNOWN
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component

from tests.components.atag import UID, init_integration
from tests.test_util.aiohttp import AiohttpClientMocker

CLIMATE_ID = f"{CLIMATE}.{DOMAIN}"


async def test_climate(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the creation and values of Atag climate device."""
    with patch("pyatag.entities.Climate.status"):
        entry = await init_integration.opp, aioclient_mock)
        registry = await.opp.helpers.entity_registry.async_get_registry()

        assert registry.async_is_registered(CLIMATE_ID)
        entry = registry.async_get(CLIMATE_ID)
        assert entry.unique_id == f"{UID}-{CLIMATE}"
        assert (
           .opp.states.get(CLIMATE_ID).attributes[ATTR_HVAC_ACTION]
            == CURRENT_HVAC_HEAT
        )


async def test_setting_climate(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test setting the climate device."""
    await init_integration.opp, aioclient_mock)
    with patch("pyatag.entities.Climate.set_temp") as mock_set_temp:
        await.opp.services.async_call(
            CLIMATE,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: CLIMATE_ID, ATTR_TEMPERATURE: 15},
            blocking=True,
        )
        await.opp.async_block_till_done()
        mock_set_temp.assert_called_once_with(15)

    with patch("pyatag.entities.Climate.set_preset_mode") as mock_set_preset:
        await.opp.services.async_call(
            CLIMATE,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: CLIMATE_ID, ATTR_PRESET_MODE: PRESET_AWAY},
            blocking=True,
        )
        await.opp.async_block_till_done()
        mock_set_preset.assert_called_once_with(PRESET_AWAY)

    with patch("pyatag.entities.Climate.set_hvac_mode") as mock_set_hvac:
        await.opp.services.async_call(
            CLIMATE,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: CLIMATE_ID, ATTR_HVAC_MODE: HVAC_MODE_HEAT},
            blocking=True,
        )
        await.opp.async_block_till_done()
        mock_set_hvac.assert_called_once_with(HVAC_MODE_HEAT)


async def test_incorrect_modes(
    opp: OpenPeerPower,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test incorrect values are handled correctly."""
    with patch(
        "pyatag.entities.Climate.hvac_mode",
        new_callable=PropertyMock(return_value="bug"),
    ):
        await init_integration.opp, aioclient_mock)
        assert.opp.states.get(CLIMATE_ID).state == STATE_UNKNOWN


async def test_update_service(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the updater service is called."""
    await init_integration.opp, aioclient_mock)
    await async_setup_component.opp, HA_DOMAIN, {})
    with patch("pyatag.AtagOne.update") as updater:
        await.opp.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: CLIMATE_ID},
            blocking=True,
        )
        await.opp.async_block_till_done()
        updater.assert_called_once()
