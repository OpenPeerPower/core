"""Test HomematicIP Cloud accesspoint."""

from unittest.mock import Mock, patch

from homematicip.aio.auth import AsyncAuth
from homematicip.base.base_connection import HmipConnectionError
import pytest

from openpeerpower.components.homematicip_cloud import DOMAIN as HMIPC_DOMAIN
from openpeerpower.components.homematicip_cloud.const import (
    HMIPC_AUTHTOKEN,
    HMIPC_HAPID,
    HMIPC_NAME,
    HMIPC_PIN,
)
from openpeerpower.components.homematicip_cloud.errors import HmipcConnectionError
from openpeerpower.components.homematicip_cloud.hap import (
    HomematicipAuth,
    HomematicipHAP,
)
from openpeerpower.config_entries import ENTRY_STATE_NOT_LOADED
from openpeerpower.exceptions import ConfigEntryNotReady

from .helper import HAPID, HAPPIN


async def test_auth_setup_opp):
    """Test auth setup for client registration."""
    config = {HMIPC_HAPID: "ABC123", HMIPC_PIN: "123", HMIPC_NAME: "hmip"}
    hmip_auth = HomematicipAuth.opp, config)
    with patch.object(hmip_auth, "get_auth"):
        assert await hmip_auth.async_setup()


async def test_auth_setup_connection_error(opp):
    """Test auth setup connection error behaviour."""
    config = {HMIPC_HAPID: "ABC123", HMIPC_PIN: "123", HMIPC_NAME: "hmip"}
    hmip_auth = HomematicipAuth.opp, config)
    with patch.object(hmip_auth, "get_auth", side_effect=HmipcConnectionError):
        assert not await hmip_auth.async_setup()


async def test_auth_auth_check_and_register.opp):
    """Test auth client registration."""
    config = {HMIPC_HAPID: "ABC123", HMIPC_PIN: "123", HMIPC_NAME: "hmip"}

    hmip_auth = HomematicipAuth.opp, config)
    hmip_auth.auth = Mock(spec=AsyncAuth)
    with patch.object(
        hmip_auth.auth, "isRequestAcknowledged", return_value=True
    ), patch.object(
        hmip_auth.auth, "requestAuthToken", return_value="ABC"
    ), patch.object(
        hmip_auth.auth, "confirmAuthToken"
    ):
        assert await hmip_auth.async_checkbutton()
        assert await hmip_auth.async_register() == "ABC"


async def test_auth_auth_check_and_register_with_exception.opp):
    """Test auth client registration."""
    config = {HMIPC_HAPID: "ABC123", HMIPC_PIN: "123", HMIPC_NAME: "hmip"}
    hmip_auth = HomematicipAuth.opp, config)
    hmip_auth.auth = Mock(spec=AsyncAuth)
    with patch.object(
        hmip_auth.auth, "isRequestAcknowledged", side_effect=HmipConnectionError
    ), patch.object(
        hmip_auth.auth, "requestAuthToken", side_effect=HmipConnectionError
    ):
        assert not await hmip_auth.async_checkbutton()
        assert await hmip_auth.async_register() is False


async def test_hap_setup_works():
    """Test a successful setup of a accesspoint."""
   opp = Mock()
    entry = Mock()
    home = Mock()
    entry.data = {HMIPC_HAPID: "ABC123", HMIPC_AUTHTOKEN: "123", HMIPC_NAME: "hmip"}
    hap = HomematicipHAP.opp, entry)
    with patch.object(hap, "get_hap", return_value=home):
        assert await hap.async_setup()

    assert hap.home is home
    assert len(opp.config_entries.async_forward_entry_setup.mock_calls) == 8
    assert opp.config_entries.async_forward_entry_setup.mock_calls[0][1] == (
        entry,
        "alarm_control_panel",
    )
    assert opp.config_entries.async_forward_entry_setup.mock_calls[1][1] == (
        entry,
        "binary_sensor",
    )


async def test_hap_setup_connection_error():
    """Test a failed accesspoint setup."""
   opp = Mock()
    entry = Mock()
    entry.data = {HMIPC_HAPID: "ABC123", HMIPC_AUTHTOKEN: "123", HMIPC_NAME: "hmip"}
    hap = HomematicipHAP.opp, entry)
    with patch.object(hap, "get_hap", side_effect=HmipcConnectionError), pytest.raises(
        ConfigEntryNotReady
    ):
        assert not await hap.async_setup()

    assert not opp.async_add_job.mock_calls
    assert not opp.config_entries.flow.async_init.mock_calls


async def test_hap_reset_unloads_entry_if_setup_opp, default_mock_hap_factory):
    """Test calling reset while the entry has been setup."""
    mock_hap = await default_mock_hap_factory.async_get_mock_hap()
    assert opp.data[HMIPC_DOMAIN][HAPID] == mock_hap
    config_entries = opp.config_entries.async_entries(HMIPC_DOMAIN)
    assert len(config_entries) == 1
    # hap_reset is called during unload
    await opp.config_entries.async_unload(config_entries[0].entry_id)
    # entry is unloaded
    assert config_entries[0].state == ENTRY_STATE_NOT_LOADED
    assert opp.data[HMIPC_DOMAIN] == {}


async def test_hap_create(opp, hmip_config_entry, simple_mock_home):
    """Mock AsyncHome to execute get_hap."""
    opp.config.components.add(HMIPC_DOMAIN)
    hap = HomematicipHAP.opp, hmip_config_entry)
    assert hap
    with patch.object(hap, "async_connect"):
        assert await hap.async_setup()


async def test_hap_create_exception(opp, hmip_config_entry, mock_connection_init):
    """Mock AsyncHome to execute get_hap."""
    opp.config.components.add(HMIPC_DOMAIN)

    hap = HomematicipHAP.opp, hmip_config_entry)
    assert hap

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncHome.get_current_state",
        side_effect=Exception,
    ):
        assert not await hap.async_setup()

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncHome.get_current_state",
        side_effect=HmipConnectionError,
    ), pytest.raises(ConfigEntryNotReady):
        await hap.async_setup()


async def test_auth_create(opp, simple_mock_auth):
    """Mock AsyncAuth to execute get_auth."""
    config = {HMIPC_HAPID: HAPID, HMIPC_PIN: HAPPIN, HMIPC_NAME: "hmip"}
    hmip_auth = HomematicipAuth.opp, config)
    assert hmip_auth

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncAuth",
        return_value=simple_mock_auth,
    ):
        assert await hmip_auth.async_setup()
        await opp.async_block_till_done()
        assert hmip_auth.auth.pin == HAPPIN


async def test_auth_create_exception(opp, simple_mock_auth):
    """Mock AsyncAuth to execute get_auth."""
    config = {HMIPC_HAPID: HAPID, HMIPC_PIN: HAPPIN, HMIPC_NAME: "hmip"}
    hmip_auth = HomematicipAuth.opp, config)
    simple_mock_auth.connectionRequest.side_effect = HmipConnectionError
    assert hmip_auth
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncAuth",
        return_value=simple_mock_auth,
    ):
        assert not await hmip_auth.async_setup()

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.AsyncAuth",
        return_value=simple_mock_auth,
    ):
        assert not await hmip_auth.get_auth(opp, HAPID, HAPPIN)
