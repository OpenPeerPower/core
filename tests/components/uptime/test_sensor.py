"""The tests for the uptime sensor platform."""

from openpeerpowerr.setup import async_setup_component


async def test_uptime_sensor_name_change.opp):
    """Test uptime sensor with different name."""
    config = {"sensor": {"platform": "uptime", "name": "foobar"}}
    assert await async_setup_component.opp, "sensor", config)
    await opp.async_block_till_done()
    assert.opp.states.get("sensor.foobar")
