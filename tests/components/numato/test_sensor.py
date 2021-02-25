"""Tests for the numato sensor platform."""
from openpeerpower.const import STATE_UNKNOWN
from openpeerpower.helpers import discovery
from openpeerpower.setup import async_setup_component

from .common import NUMATO_CFG, mockup_raise

MOCKUP_ENTITY_IDS = {
    "sensor.numato_adc_mock_port1",
}


async def test_failing_setups_no_entities(opp, numato_fixture, monkeypatch):
    """When port setup fails, no entity shall be created."""
    monkeypatch.setattr(numato_fixture.NumatoDeviceMock, "setup", mockup_raise)
    assert await async_setup_component(opp, "numato", NUMATO_CFG)
    await opp.async_block_till_done()
    for entity_id in MOCKUP_ENTITY_IDS:
        assert entity_id not in opp.states.async_entity_ids()


async def test_failing_sensor_update(opp, numato_fixture, monkeypatch):
    """Test condition when a sensor update fails."""
    monkeypatch.setattr(numato_fixture.NumatoDeviceMock, "adc_read", mockup_raise)
    assert await async_setup_component(opp, "numato", NUMATO_CFG)
    await opp.async_block_till_done()
    assert opp.states.get("sensor.numato_adc_mock_port1").state is STATE_UNKNOWN


async def test_sensor_setup_without_discovery_info(opp, config, numato_fixture):
    """Test handling of empty discovery_info."""
    numato_fixture.discover()
    await discovery.async_load_platform(opp, "sensor", "numato", None, config)
    for entity_id in MOCKUP_ENTITY_IDS:
        assert entity_id not in opp.states.async_entity_ids()
    await opp.async_block_till_done()  # wait for numato platform to be loaded
    for entity_id in MOCKUP_ENTITY_IDS:
        assert entity_id in opp.states.async_entity_ids()
