"""Test Hue init with multiple bridges."""
from unittest.mock import patch

import pytest

from openpeerpower.components import hue
from openpeerpower.setup import async_setup_component

from .conftest import create_mock_bridge

from tests.common import MockConfigEntry


async def setup_component(opp):
    """Hue component."""
    with patch.object(hue, "async_setup_entry", return_value=True):
        assert (
            await async_setup_component(
                opp,
                hue.DOMAIN,
                {},
            )
            is True
        )


async def test_hue_activate_scene_both_responds(
    opp, mock_bridge1, mock_bridge2, mock_config_entry1, mock_config_entry2
):
    """Test that makes both bridges successfully activate a scene."""

    await setup_component(opp)

    await setup_bridge(opp, mock_bridge1, mock_config_entry1)
    await setup_bridge(opp, mock_bridge2, mock_config_entry2)

    with patch.object(
        mock_bridge1, "hue_activate_scene", return_value=None
    ) as mock_hue_activate_scene1, patch.object(
        mock_bridge2, "hue_activate_scene", return_value=None
    ) as mock_hue_activate_scene2:
        await opp.services.async_call(
            "hue",
            "hue_activate_scene",
            {"group_name": "group_2", "scene_name": "my_scene"},
            blocking=True,
        )

    mock_hue_activate_scene1.assert_called_once()
    mock_hue_activate_scene2.assert_called_once()


async def test_hue_activate_scene_one_responds(
    opp, mock_bridge1, mock_bridge2, mock_config_entry1, mock_config_entry2
):
    """Test that makes only one bridge successfully activate a scene."""

    await setup_component(opp)

    await setup_bridge(opp, mock_bridge1, mock_config_entry1)
    await setup_bridge(opp, mock_bridge2, mock_config_entry2)

    with patch.object(
        mock_bridge1, "hue_activate_scene", return_value=None
    ) as mock_hue_activate_scene1, patch.object(
        mock_bridge2, "hue_activate_scene", return_value=False
    ) as mock_hue_activate_scene2:
        await opp.services.async_call(
            "hue",
            "hue_activate_scene",
            {"group_name": "group_2", "scene_name": "my_scene"},
            blocking=True,
        )

    mock_hue_activate_scene1.assert_called_once()
    mock_hue_activate_scene2.assert_called_once()


async def test_hue_activate_scene_zero_responds(
    opp, mock_bridge1, mock_bridge2, mock_config_entry1, mock_config_entry2
):
    """Test that makes no bridge successfully activate a scene."""

    await setup_component(opp)

    await setup_bridge(opp, mock_bridge1, mock_config_entry1)
    await setup_bridge(opp, mock_bridge2, mock_config_entry2)

    with patch.object(
        mock_bridge1, "hue_activate_scene", return_value=False
    ) as mock_hue_activate_scene1, patch.object(
        mock_bridge2, "hue_activate_scene", return_value=False
    ) as mock_hue_activate_scene2:
        await opp.services.async_call(
            "hue",
            "hue_activate_scene",
            {"group_name": "group_2", "scene_name": "my_scene"},
            blocking=True,
        )

    # both were retried
    assert mock_hue_activate_scene1.call_count == 2
    assert mock_hue_activate_scene2.call_count == 2


async def setup_bridge(opp, mock_bridge, config_entry):
    """Load the Hue light platform with the provided bridge."""
    mock_bridge.config_entry = config_entry
    config_entry.add_to_opp(opp)
    with patch("openpeerpower.components.hue.HueBridge", return_value=mock_bridge):
        await opp.config_entries.async_setup(config_entry.entry_id)


@pytest.fixture
def mock_config_entry1(opp):
    """Mock a config entry."""
    return create_config_entry()


@pytest.fixture
def mock_config_entry2(opp):
    """Mock a config entry."""
    return create_config_entry()


def create_config_entry():
    """Mock a config entry."""
    return MockConfigEntry(
        domain=hue.DOMAIN,
        data={"host": "mock-host"},
    )


@pytest.fixture
def mock_bridge1(opp):
    """Mock a Hue bridge."""
    return create_mock_bridge(opp)


@pytest.fixture
def mock_bridge2(opp):
    """Mock a Hue bridge."""
    return create_mock_bridge(opp)
