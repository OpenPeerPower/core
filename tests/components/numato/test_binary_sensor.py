"""Tests for the numato binary_sensor platform."""
from openpeerpower.helpers import discovery
from openpeerpower.setup import async_setup_component

from .common import NUMATO_CFG, mockup_raise

MOCKUP_ENTITY_IDS = {
    "binary_sensor.numato_binary_sensor_mock_port2",
    "binary_sensor.numato_binary_sensor_mock_port3",
    "binary_sensor.numato_binary_sensor_mock_port4",
}


async def test_failing_setups_no_entities(opp, numato_fixture, monkeypatch):
    """When port setup fails, no entity shall be created."""
    monkeypatch.setattr(numato_fixture.NumatoDeviceMock, "setup", mockup_raise)
    assert await async_setup_component(opp, "numato", NUMATO_CFG)
    await opp.async_block_till_done()
    for entity_id in MOCKUP_ENTITY_IDS:
        assert entity_id not in opp.states.async_entity_ids()


async def test_setup_callbacks(opp, numato_fixture, monkeypatch):
    """During setup a callback shall be registered."""

    numato_fixture.discover()

    def mock_add_event_detect(self, port, callback, direction):
        assert self == numato_fixture.devices[0]
        assert port == 1
        assert callback is callable
        assert direction == numato_fixture.BOTH

    monkeypatch.setattr(
        numato_fixture.devices[0], "add_event_detect", mock_add_event_detect
    )
    assert await async_setup_component(opp, "numato", NUMATO_CFG)


async def test_opp_binary_sensor_notification(opp, numato_fixture):
    """Test regular operations from within Open Peer Power."""
    assert await async_setup_component(opp, "numato", NUMATO_CFG)
    await opp.async_block_till_done()  # wait until services are registered
    assert opp.states.get("binary_sensor.numato_binary_sensor_mock_port2").state == "on"
    await opp.async_add_executor_job(numato_fixture.devices[0].callbacks[2], 2, False)
    await opp.async_block_till_done()
    assert (
        opp.states.get("binary_sensor.numato_binary_sensor_mock_port2").state == "off"
    )


async def test_binary_sensor_setup_without_discovery_info(opp, config, numato_fixture):
    """Test handling of empty discovery_info."""
    numato_fixture.discover()
    await discovery.async_load_platform(opp, "binary_sensor", "numato", None, config)
    for entity_id in MOCKUP_ENTITY_IDS:
        assert entity_id not in opp.states.async_entity_ids()
    await opp.async_block_till_done()  # wait for numato platform to be loaded
    for entity_id in MOCKUP_ENTITY_IDS:
        assert entity_id in opp.states.async_entity_ids()
