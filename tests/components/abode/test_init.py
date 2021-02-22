"""Tests for the Abode module."""
from unittest.mock import patch

from abodepy.exceptions import AbodeAuthenticationException

from openpeerpower.components.abode import (
    DOMAIN as ABODE_DOMAIN,
    SERVICE_CAPTURE_IMAGE,
    SERVICE_SETTINGS,
    SERVICE_TRIGGER_AUTOMATION,
)
from openpeerpower.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from openpeerpower.const import CONF_USERNAME, HTTP_BAD_REQUEST

from .common import setup_platform


async def test_change_settings.opp):
    """Test change_setting service."""
    await setup_platform.opp, ALARM_DOMAIN)

    with patch("abodepy.Abode.set_setting") as mock_set_setting:
        await opp.services.async_call(
            ABODE_DOMAIN,
            SERVICE_SETTINGS,
            {"setting": "confirm_snd", "value": "loud"},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_set_setting.assert_called_once()


async def test_add_unique_id.opp):
    """Test unique_id is set to Abode username."""
    mock_entry = await setup_platform.opp, ALARM_DOMAIN)
    # Set unique_id to None to match previous config entries
   .opp.config_entries.async_update_entry(entry=mock_entry, unique_id=None)
    await opp.async_block_till_done()

    assert mock_entry.unique_id is None

    with patch("abodepy.UTILS"):
        await opp.config_entries.async_reload(mock_entry.entry_id)
        await opp.async_block_till_done()

    assert mock_entry.unique_id == mock_entry.data[CONF_USERNAME]


async def test_unload_entry.opp):
    """Test unloading the Abode entry."""
    mock_entry = await setup_platform.opp, ALARM_DOMAIN)

    with patch("abodepy.Abode.logout") as mock_logout, patch(
        "abodepy.event_controller.AbodeEventController.stop"
    ) as mock_events_stop:
        assert await opp.config_entries.async_unload(mock_entry.entry_id)
        mock_logout.assert_called_once()
        mock_events_stop.assert_called_once()

        assert not.opp.services.has_service(ABODE_DOMAIN, SERVICE_SETTINGS)
        assert not.opp.services.has_service(ABODE_DOMAIN, SERVICE_CAPTURE_IMAGE)
        assert not.opp.services.has_service(ABODE_DOMAIN, SERVICE_TRIGGER_AUTOMATION)


async def test_invalid_credentials.opp):
    """Test Abode credentials changing."""
    with patch(
        "openpeerpower.components.abode.Abode",
        side_effect=AbodeAuthenticationException((HTTP_BAD_REQUEST, "auth error")),
    ), patch(
        "openpeerpower.components.abode.config_flow.AbodeFlowHandler.async_step_reauth"
    ) as mock_async_step_reauth:
        await setup_platform.opp, ALARM_DOMAIN)

        mock_async_step_reauth.assert_called_once()
