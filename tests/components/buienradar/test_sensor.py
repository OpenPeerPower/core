"""The tests for the Buienradar sensor platform."""
from openpeerpower.components import sensor
from openpeerpower.setup import async_setup_component

CONDITIONS = ["stationname", "temperature"]
BASE_CONFIG = {
    "sensor": [
        {
            "platform": "buienradar",
            "name": "volkel",
            "latitude": 51.65,
            "longitude": 5.7,
            "monitored_conditions": CONDITIONS,
        }
    ]
}


async def test_smoke_test_setup_component(opp):
    """Smoke test for successfully set-up with default config."""
    assert await async_setup_component(opp, sensor.DOMAIN, BASE_CONFIG)
    await opp.async_block_till_done()

    for cond in CONDITIONS:
        state = opp.states.get(f"sensor.volkel_{cond}")
        assert state.state == "unknown"
