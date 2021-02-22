"""Test Google report state."""
from unittest.mock import AsyncMock, patch

from openpeerpower.components.google_assistant import error, report_state
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from . import BASIC_CONFIG

from tests.common import async_fire_time_changed


async def test_report_state.opp, caplog, legacy_patchable_time):
    """Test report state works."""
    assert await async_setup_component.opp, "switch", {})
    opp.states.async_set("light.ceiling", "off")
    opp.states.async_set("switch.ac", "on")

    with patch.object(
        BASIC_CONFIG, "async_report_state_all", AsyncMock()
    ) as mock_report, patch.object(report_state, "INITIAL_REPORT_DELAY", 0):
        unsub = report_state.async_enable_report_state.opp, BASIC_CONFIG)

        async_fire_time_changed.opp, utcnow())
        await opp.async_block_till_done()

    # Test that enabling report state does a report on all entities
    assert len(mock_report.mock_calls) == 1
    assert mock_report.mock_calls[0][1][0] == {
        "devices": {
            "states": {
                "light.ceiling": {"on": False, "online": True},
                "switch.ac": {"on": True, "online": True},
            }
        }
    }

    with patch.object(
        BASIC_CONFIG, "async_report_state_all", AsyncMock()
    ) as mock_report:
        opp.states.async_set("light.kitchen", "on")
        await opp.async_block_till_done()

    assert len(mock_report.mock_calls) == 1
    assert mock_report.mock_calls[0][1][0] == {
        "devices": {"states": {"light.kitchen": {"on": True, "online": True}}}
    }

    # Test that if serialize returns same value, we don't send
    with patch(
        "openpeerpower.components.google_assistant.report_state.GoogleEntity.query_serialize",
        return_value={"same": "info"},
    ), patch.object(BASIC_CONFIG, "async_report_state_all", AsyncMock()) as mock_report:
        # New state, so reported
        opp.states.async_set("light.double_report", "on")
        await opp.async_block_till_done()

        # Changed, but serialize is same, so filtered out by extra check
        opp.states.async_set("light.double_report", "off")
        await opp.async_block_till_done()

        assert len(mock_report.mock_calls) == 1
        assert mock_report.mock_calls[0][1][0] == {
            "devices": {"states": {"light.double_report": {"same": "info"}}}
        }

    # Test that only significant state changes are reported
    with patch.object(
        BASIC_CONFIG, "async_report_state_all", AsyncMock()
    ) as mock_report:
        opp.states.async_set("switch.ac", "on", {"something": "else"})
        await opp.async_block_till_done()

    assert len(mock_report.mock_calls) == 0

    # Test that entities that we can't query don't report a state
    with patch.object(
        BASIC_CONFIG, "async_report_state_all", AsyncMock()
    ) as mock_report, patch(
        "openpeerpower.components.google_assistant.report_state.GoogleEntity.query_serialize",
        side_effect=error.SmartHomeError("mock-error", "mock-msg"),
    ):
        opp.states.async_set("light.kitchen", "off")
        await opp.async_block_till_done()

    assert "Not reporting state for light.kitchen: mock-error"
    assert len(mock_report.mock_calls) == 0

    unsub()

    with patch.object(
        BASIC_CONFIG, "async_report_state_all", AsyncMock()
    ) as mock_report:
        opp.states.async_set("light.kitchen", "on")
        await opp.async_block_till_done()

    assert len(mock_report.mock_calls) == 0
