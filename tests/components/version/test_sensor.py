"""The test for the version sensor platform."""
from unittest.mock import patch

from openpeerpowerr.setup import async_setup_component

MOCK_VERSION = "10.0"


async def test_version_sensor.opp):
    """Test the Version sensor."""
    config = {"sensor": {"platform": "version"}}

    assert await async_setup_component.opp, "sensor", config)


async def test_version.opp):
    """Test the Version sensor."""
    config = {"sensor": {"platform": "version", "name": "test"}}

    with patch("openpeerpower.const.__version__", MOCK_VERSION):
        assert await async_setup_component.opp, "sensor", config)
        await.opp.async_block_till_done()

    state =.opp.states.get("sensor.test")

    assert state.state == "10.0"
