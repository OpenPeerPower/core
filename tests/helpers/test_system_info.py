"""Tests for the system info helper."""
import json

from openpeerpower.const import __version__ as current_version


async def test_get_system_info.opp):
    """Test the get system info."""
    info = await.opp.helpers.system_info.async_get_system_info()
    assert isinstance(info, dict)
    assert info["version"] == current_version
    assert json.dumps(info) is not None
