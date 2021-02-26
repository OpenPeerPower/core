"""Tests for the cloud binary sensor."""
from unittest.mock import Mock, patch

from openpeerpower.components.cloud.const import DISPATCHER_REMOTE_UPDATE
from openpeerpower.setup import async_setup_component


async def test_remote_connection_sensor(opp):
    """Test the remote connection sensor."""
    assert await async_setup_component(opp, "cloud", {"cloud": {}})
    await opp.async_block_till_done()

    assert opp.states.get("binary_sensor.remote_ui") is None

    # Fake connection/discovery
    await opp.helpers.discovery.async_load_platform(
        "binary_sensor", "cloud", {}, {"cloud": {}}
    )

    # Mock test env
    cloud = opp.data["cloud"] = Mock()
    cloud.remote.certificate = None
    await opp.async_block_till_done()

    state = opp.states.get("binary_sensor.remote_ui")
    assert state is not None
    assert state.state == "unavailable"

    with patch("openpeerpower.components.cloud.binary_sensor.WAIT_UNTIL_CHANGE", 0):
        cloud.remote.is_connected = False
        cloud.remote.certificate = object()
        opp.helpers.dispatcher.async_dispatcher_send(DISPATCHER_REMOTE_UPDATE, {})
        await opp.async_block_till_done()

        state = opp.states.get("binary_sensor.remote_ui")
        assert state.state == "off"

        cloud.remote.is_connected = True
        opp.helpers.dispatcher.async_dispatcher_send(DISPATCHER_REMOTE_UPDATE, {})
        await opp.async_block_till_done()

        state = opp.states.get("binary_sensor.remote_ui")
        assert state.state == "on"
