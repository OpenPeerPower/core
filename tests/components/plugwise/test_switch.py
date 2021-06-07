"""Tests for the Plugwise switch integration."""

from plugwise.exceptions import PlugwiseException

from openpeerpower.config_entries import ConfigEntryState

from tests.components.plugwise.common import async_init_integration


async def test_adam_climate_switch_entities(opp, mock_smile_adam):
    """Test creation of climate related switch entities."""
    entry = await async_init_integration(opp, mock_smile_adam)
    assert entry.state is ConfigEntryState.LOADED

    state = opp.states.get("switch.cv_pomp")
    assert str(state.state) == "on"

    state = opp.states.get("switch.fibaro_hc2")
    assert str(state.state) == "on"


async def test_adam_climate_switch_negative_testing(opp, mock_smile_adam):
    """Test exceptions of climate related switch entities."""
    mock_smile_adam.set_relay_state.side_effect = PlugwiseException
    entry = await async_init_integration(opp, mock_smile_adam)
    assert entry.state is ConfigEntryState.LOADED

    await opp.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.cv_pomp"},
        blocking=True,
    )
    state = opp.states.get("switch.cv_pomp")
    assert str(state.state) == "on"

    await opp.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.fibaro_hc2"},
        blocking=True,
    )
    state = opp.states.get("switch.fibaro_hc2")
    assert str(state.state) == "on"


async def test_adam_climate_switch_changes(opp, mock_smile_adam):
    """Test changing of climate related switch entities."""
    entry = await async_init_integration(opp, mock_smile_adam)
    assert entry.state is ConfigEntryState.LOADED

    await opp.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.cv_pomp"},
        blocking=True,
    )
    state = opp.states.get("switch.cv_pomp")
    assert str(state.state) == "off"

    await opp.services.async_call(
        "switch",
        "toggle",
        {"entity_id": "switch.fibaro_hc2"},
        blocking=True,
    )
    state = opp.states.get("switch.fibaro_hc2")
    assert str(state.state) == "off"

    await opp.services.async_call(
        "switch",
        "toggle",
        {"entity_id": "switch.fibaro_hc2"},
        blocking=True,
    )
    state = opp.states.get("switch.fibaro_hc2")
    assert str(state.state) == "on"


async def test_stretch_switch_entities(opp, mock_stretch):
    """Test creation of climate related switch entities."""
    entry = await async_init_integration(opp, mock_stretch)
    assert entry.state is ConfigEntryState.LOADED

    state = opp.states.get("switch.koelkast_92c4a")
    assert str(state.state) == "on"

    state = opp.states.get("switch.droger_52559")
    assert str(state.state) == "on"


async def test_stretch_switch_changes(opp, mock_stretch):
    """Test changing of power related switch entities."""
    entry = await async_init_integration(opp, mock_stretch)
    assert entry.state is ConfigEntryState.LOADED

    await opp.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.koelkast_92c4a"},
        blocking=True,
    )

    state = opp.states.get("switch.koelkast_92c4a")
    assert str(state.state) == "off"

    await opp.services.async_call(
        "switch",
        "toggle",
        {"entity_id": "switch.droger_52559"},
        blocking=True,
    )
    state = opp.states.get("switch.droger_52559")
    assert str(state.state) == "off"

    await opp.services.async_call(
        "switch",
        "toggle",
        {"entity_id": "switch.droger_52559"},
        blocking=True,
    )
    state = opp.states.get("switch.droger_52559")
    assert str(state.state) == "on"
