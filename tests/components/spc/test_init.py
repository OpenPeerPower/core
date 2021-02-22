"""Tests for Vanderbilt SPC component."""
from unittest.mock import Mock, PropertyMock, patch

from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components.spc import DATA_API
from openpeerpower.const import STATE_ALARM_ARMED_AWAY, STATE_ALARM_DISARMED

from tests.common import mock_coro


async def test_valid_device_config.opp, monkeypatch):
    """Test valid device config."""
    config = {"spc": {"api_url": "http://localhost/", "ws_url": "ws://localhost/"}}

    with patch(
        "openpeerpower.components.spc.SpcWebGateway.async_load_parameters",
        return_value=mock_coro(True),
    ):
        assert await async_setup_component.opp, "spc", config) is True


async def test_invalid_device_config.opp, monkeypatch):
    """Test valid device config."""
    config = {"spc": {"api_url": "http://localhost/"}}

    with patch(
        "openpeerpower.components.spc.SpcWebGateway.async_load_parameters",
        return_value=mock_coro(True),
    ):
        assert await async_setup_component.opp, "spc", config) is False


async def test_update_alarm_device.opp):
    """Test that alarm panel state changes on incoming websocket data."""
    import pyspcwebgw
    from pyspcwebgw.const import AreaMode

    config = {"spc": {"api_url": "http://localhost/", "ws_url": "ws://localhost/"}}

    area_mock = Mock(
        spec=pyspcwebgw.area.Area,
        id="1",
        mode=AreaMode.FULL_SET,
        last_changed_by="Sven",
    )
    area_mock.name = "House"
    area_mock.verified_alarm = False

    with patch(
        "openpeerpower.components.spc.SpcWebGateway.areas", new_callable=PropertyMock
    ) as mock_areas:
        mock_areas.return_value = {"1": area_mock}
        with patch(
            "openpeerpower.components.spc.SpcWebGateway.async_load_parameters",
            return_value=mock_coro(True),
        ):
            assert await async_setup_component.opp, "spc", config) is True

        await.opp.async_block_till_done()

    entity_id = "alarm_control_panel.house"

    assert.opp.states.get(entity_id).state == STATE_ALARM_ARMED_AWAY
    assert.opp.states.get(entity_id).attributes["changed_by"] == "Sven"

    area_mock.mode = AreaMode.UNSET
    area_mock.last_changed_by = "Anna"
    await.opp.data[DATA_API]._async_callback(area_mock)
    await.opp.async_block_till_done()

    assert.opp.states.get(entity_id).state == STATE_ALARM_DISARMED
    assert.opp.states.get(entity_id).attributes["changed_by"] == "Anna"
