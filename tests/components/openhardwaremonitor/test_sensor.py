"""The tests for the Open Hardware Monitor platform."""
from openpeerpower.setup import async_setup_component

from tests.common import load_fixture


async def test_setup(opp, requests_mock):
    """Test for successfully setting up the platform."""
    config = {
        "sensor": {
            "platform": "openhardwaremonitor",
            "host": "localhost",
            "port": 8085,
        }
    }

    requests_mock.get(
        "http://localhost:8085/data.json",
        text=load_fixture("openhardwaremonitor.json"),
    )

    await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()

    entities = opp.states.async_entity_ids("sensor")
    assert len(entities) == 38

    state = opp.states.get("sensor.test_pc_intel_core_i7_7700_temperatures_cpu_core_1")

    assert state is not None
    assert state.state == "31.0"

    state = opp.states.get("sensor.test_pc_intel_core_i7_7700_temperatures_cpu_core_2")

    assert state is not None
    assert state.state == "30.0"
