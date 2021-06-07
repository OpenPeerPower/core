"""Test the devolo_home_control config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.devolo_home_control.const import DEFAULT_MYDEVOLO, DOMAIN
from openpeerpower.config_entries import SOURCE_USER

from .const import (
    DISCOVERY_INFO,
    DISCOVERY_INFO_WRONG_DEVICE,
    DISCOVERY_INFO_WRONG_DEVOLO_DEVICE,
)

from tests.common import MockConfigEntry


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    await _setup(opp, result)


@pytest.mark.credentials_invalid
async def test_form_invalid_credentials_user(opp):
    """Test if we get the error message on invalid credentials."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "test-username", "password": "test-password"},
    )

    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_already_configured(opp):
    """Test if we get the error message on already configured."""
    with patch(
        "openpeerpower.components.devolo_home_control.Mydevolo.uuid",
        return_value="123456",
    ):
        MockConfigEntry(domain=DOMAIN, unique_id="123456", data={}).add_to_opp(opp)
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"username": "test-username", "password": "test-password"},
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "already_configured"


async def test_form_advanced_options(opp):
    """Test if we get the advanced options if user has enabled it."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.devolo_home_control.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.devolo_home_control.Mydevolo.uuid",
        return_value="123456",
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "mydevolo_url": "https://test_mydevolo_url.test",
            },
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "devolo Home Control"
    assert result2["data"] == {
        "username": "test-username",
        "password": "test-password",
        "mydevolo_url": "https://test_mydevolo_url.test",
    }

    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_zeroconf(opp):
    """Test that the zeroconf confirmation form is served."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    await _setup(opp, result)


@pytest.mark.credentials_invalid
async def test_form_invalid_credentials_zeroconf(opp):
    """Test if we get the error message on invalid credentials."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "test-username", "password": "test-password"},
    )

    assert result["errors"] == {"base": "invalid_auth"}


async def test_zeroconf_wrong_device(opp):
    """Test that the zeroconf ignores wrong devices."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_WRONG_DEVOLO_DEVICE,
    )

    assert result["reason"] == "Not a devolo Home Control gateway."
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_WRONG_DEVICE,
    )

    assert result["reason"] == "Not a devolo Home Control gateway."
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def _setup(opp, result):
    """Finish configuration steps."""
    with patch(
        "openpeerpower.components.devolo_home_control.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.devolo_home_control.Mydevolo.uuid",
        return_value="123456",
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "devolo Home Control"
    assert result2["data"] == {
        "username": "test-username",
        "password": "test-password",
        "mydevolo_url": DEFAULT_MYDEVOLO,
    }

    assert len(mock_setup_entry.mock_calls) == 1
