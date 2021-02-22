"""Test the SmartHab config flow."""
from unittest.mock import patch

import pysmarthab

from openpeerpower import config_entries, setup
from openpeerpower.components.smarthab import DOMAIN
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch("pysmarthab.SmartHab.async_login"), patch(
        "pysmarthab.SmartHab.is_logged_in", return_value=True
    ), patch(
        "openpeerpower.components.smarthab.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.smarthab.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "mock@example.com", CONF_PASSWORD: "test-password"},
        )
        await.opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "mock@example.com"
    assert result2["data"] == {
        CONF_EMAIL: "mock@example.com",
        CONF_PASSWORD: "test-password",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("pysmarthab.SmartHab.async_login"), patch(
        "pysmarthab.SmartHab.is_logged_in", return_value=False
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "mock@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_service_error(opp):
    """Test we handle service errors."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "pysmarthab.SmartHab.async_login",
        side_effect=pysmarthab.RequestFailedException(42),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "mock@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "service"}


async def test_form_unknown_error(opp):
    """Test we handle unknown errors."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "pysmarthab.SmartHab.async_login",
        side_effect=Exception,
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "mock@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_import.opp):
    """Test import."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    imported_conf = {
        CONF_EMAIL: "mock@example.com",
        CONF_PASSWORD: "test-password",
    }

    with patch("pysmarthab.SmartHab.async_login"), patch(
        "pysmarthab.SmartHab.is_logged_in", return_value=True
    ), patch(
        "openpeerpower.components.smarthab.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.smarthab.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=imported_conf
        )
        await.opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "mock@example.com"
    assert result["data"] == {
        CONF_EMAIL: "mock@example.com",
        CONF_PASSWORD: "test-password",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
