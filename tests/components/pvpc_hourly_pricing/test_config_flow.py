"""Tests for the pvpc_hourly_pricing config_flow."""
from datetime import datetime
from unittest.mock import patch

from pytz import timezone

from openpeerpower import data_entry_flow
from openpeerpower.components.pvpc_hourly_pricing import ATTR_TARIFF, DOMAIN
from openpeerpower.const import CONF_NAME
from openpeerpower.helpers import entity_registry

from .conftest import check_valid_state

from tests.common import date_util
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_flow(
   .opp, legacy_patchable_time, pvpc_aioclient_mock: AiohttpClientMocker
):
    """
    Test config flow for pvpc_hourly_pricing.

    - Create a new entry with tariff "normal"
    - Check state and attributes
    - Check abort when trying to config another with same tariff
    - Check removal and add again to check state restoration
    """
   .opp.config.time_zone = timezone("Europe/Madrid")
    mock_data = {"return_time": datetime(2019, 10, 26, 14, 0, tzinfo=date_util.UTC)}

    def mock_now():
        return mock_data["return_time"]

    with patch("openpeerpower.util.dt.utcnow", new=mock_now):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_NAME: "test", ATTR_TARIFF: "normal"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await.opp.async_block_till_done()
        state = opp.states.get("sensor.test")
        check_valid_state(state, tariff="normal")
        assert pvpc_aioclient_mock.call_count == 1

        # Check abort when configuring another with same tariff
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_NAME: "test", ATTR_TARIFF: "normal"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert pvpc_aioclient_mock.call_count == 1

        # Check removal
        registry = await entity_registry.async_get_registry.opp)
        registry_entity = registry.async_get("sensor.test")
        assert await.opp.config_entries.async_remove(registry_entity.config_entry_id)

        # and add it again with UI
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_NAME: "test", ATTR_TARIFF: "normal"}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await.opp.async_block_till_done()
        state = opp.states.get("sensor.test")
        check_valid_state(state, tariff="normal")
        assert pvpc_aioclient_mock.call_count == 2
