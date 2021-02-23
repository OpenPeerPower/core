"""Test the Smart Meter Texas sensor entity."""
from unittest.mock import patch

from openpeerpower.components.openpeerpower import (
    DOMAIN as OP_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from openpeerpower.components.smart_meter_texas.const import (
    ELECTRIC_METER,
    ESIID,
    METER_NUMBER,
)
from openpeerpower.const import ATTR_ENTITY_ID, CONF_ADDRESS
from openpeerpower.setup import async_setup_component

from .conftest import TEST_ENTITY_ID, refresh_data, setup_integration


async def test_sensor.opp, config_entry, aioclient_mock):
    """Test that the sensor is setup."""
    await setup_integration.opp, config_entry, aioclient_mock)
    await refresh_data.opp, config_entry, aioclient_mock)
    meter = opp.states.get(TEST_ENTITY_ID)

    assert meter
    assert meter.state == "9751.212"


async def test_name.opp, config_entry, aioclient_mock):
    """Test sensor name property."""
    await setup_integration.opp, config_entry, aioclient_mock)
    await refresh_data.opp, config_entry, aioclient_mock)
    meter = opp.states.get(TEST_ENTITY_ID)

    assert meter.name == f"{ELECTRIC_METER} 123456789"


async def test_attributes.opp, config_entry, aioclient_mock):
    """Test meter attributes."""
    await setup_integration.opp, config_entry, aioclient_mock)
    await refresh_data.opp, config_entry, aioclient_mock)
    meter = opp.states.get(TEST_ENTITY_ID)

    assert meter.attributes[METER_NUMBER] == "123456789"
    assert meter.attributes[ESIID] == "12345678901234567"
    assert meter.attributes[CONF_ADDRESS] == "123 MAIN ST"


async def test_generic_entity_update_service.opp, config_entry, aioclient_mock):
    """Test generic update entity service homeasasistant/update_entity."""
    await setup_integration.opp, config_entry, aioclient_mock)
    await async_setup_component.opp, OP_DOMAIN, {})
    with patch("smart_meter_texas.Meter.read_meter") as updater:
        await opp.services.async_call(
            OP_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID},
            blocking=True,
        )
        await opp.async_block_till_done()
        updater.assert_called_once()
