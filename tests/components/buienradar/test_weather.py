"""The tests for the buienradar weather component."""
from openpeerpower.components import weather
from openpeerpowerr.setup import async_setup_component

# Example config snippet from documentation.
BASE_CONFIG = {
    "weather": [
        {
            "platform": "buienradar",
            "name": "volkel",
            "latitude": 51.65,
            "longitude": 5.7,
            "forecast": True,
        }
    ]
}


async def test_smoke_test_setup_component.opp):
    """Smoke test for successfully set-up with default config."""
    assert await async_setup_component.opp, weather.DOMAIN, BASE_CONFIG)
    await opp..async_block_till_done()

    state = opp.states.get("weather.volkel")
    assert state.state == "unknown"
