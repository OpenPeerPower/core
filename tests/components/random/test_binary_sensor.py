"""The test for the Random binary sensor platform."""
from unittest.mock import patch

from openpeerpower.setup import async_setup_component


async def test_random_binary_sensor_on.opp):
    """Test the Random binary sensor."""
    config = {"binary_sensor": {"platform": "random", "name": "test"}}

    with patch(
        "openpeerpower.components.random.binary_sensor.getrandbits",
        return_value=1,
    ):
        assert await async_setup_component(
           .opp,
            "binary_sensor",
            config,
        )
        await.opp.async_block_till_done()

    state =.opp.states.get("binary_sensor.test")

    assert state.state == "on"


async def test_random_binary_sensor_off.opp):
    """Test the Random binary sensor."""
    config = {"binary_sensor": {"platform": "random", "name": "test"}}

    with patch(
        "openpeerpower.components.random.binary_sensor.getrandbits",
        return_value=False,
    ):
        assert await async_setup_component(
           .opp,
            "binary_sensor",
            config,
        )
        await.opp.async_block_till_done()

    state =.opp.states.get("binary_sensor.test")

    assert state.state == "off"
