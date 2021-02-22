"""Test the my init."""

from unittest import mock

from openpeerpower.components.my import URL_PATH
from openpeerpower.setup import async_setup_component


async def test_setup_opp):
    """Test setup."""
    with mock.patch(
        "openpeerpower.components.frontend.async_register_built_in_panel"
    ) as mock_register_panel:
        assert await async_setup_component.opp, "my", {"foo": "bar"})
        assert mock_register_panel.call_args == mock.call(
            opp, "my", frontend_url_path=URL_PATH
        )
