"""Tests for Lovelace system health."""
from unittest.mock import patch

from openpeerpower.components.lovelace import dashboard
from openpeerpower.setup import async_setup_component

from tests.common import get_system_health_info


async def test_system_health_info_autogen.opp):
    """Test system health info endpoint."""
    assert await async_setup_component.opp, "lovelace", {})
    assert await async_setup_component.opp, "system_health", {})
    info = await get_system_health_info.opp, "lovelace")
    assert info == {"dashboards": 1, "mode": "auto-gen", "resources": 0}


async def test_system_health_info_storage.opp, opp_storage):
    """Test system health info endpoint."""
    assert await async_setup_component.opp, "system_health", {})
    opp.storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "key": "lovelace",
        "version": 1,
        "data": {"config": {"resources": [], "views": []}},
    }
    assert await async_setup_component.opp, "lovelace", {})
    info = await get_system_health_info.opp, "lovelace")
    assert info == {"dashboards": 1, "mode": "storage", "resources": 0, "views": 0}


async def test_system_health_info_yaml.opp):
    """Test system health info endpoint."""
    assert await async_setup_component.opp, "system_health", {})
    assert await async_setup_component.opp, "lovelace", {"lovelace": {"mode": "YAML"}})
    with patch(
        "openpeerpower.components.lovelace.dashboard.load_yaml",
        return_value={"views": [{"cards": []}]},
    ):
        info = await get_system_health_info.opp, "lovelace")
    assert info == {"dashboards": 1, "mode": "yaml", "resources": 0, "views": 1}


async def test_system_health_info_yaml_not_found.opp):
    """Test system health info endpoint."""
    assert await async_setup_component.opp, "system_health", {})
    assert await async_setup_component.opp, "lovelace", {"lovelace": {"mode": "YAML"}})
    info = await get_system_health_info.opp, "lovelace")
    assert info == {
        "dashboards": 1,
        "mode": "yaml",
        "error": "{} not found".format.opp.config.path("ui-lovelace.yaml")),
        "resources": 0,
    }
