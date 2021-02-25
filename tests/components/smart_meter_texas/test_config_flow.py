"""Test the Smart Meter Texas config flow."""
import asyncio
from unittest.mock import patch

from aiohttp import ClientError
import pytest
from smart_meter_texas.exceptions import (
    SmartMeterTexasAPIError,
    SmartMeterTexasAuthError,
)

from openpeerpower import config_entries, setup
from openpeerpower.components.smart_meter_texas.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

TEST_LOGIN = {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"}


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch("smart_meter_texas.Client.authenticate", return_value=True), patch(
        "openpeerpower.components.smart_meter_texas.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.smart_meter_texas.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], TEST_LOGIN
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == TEST_LOGIN[CONF_USERNAME]
    assert result2["data"] == TEST_LOGIN
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "smart_meter_texas.Client.authenticate",
        side_effect=SmartMeterTexasAuthError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_LOGIN,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


@pytest.mark.parametrize(
    "side_effect", [asyncio.TimeoutError, ClientError, SmartMeterTexasAPIError]
)
async def test_form_cannot_connect(opp, side_effect):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "smart_meter_texas.Client.authenticate",
        side_effect=side_effect,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], TEST_LOGIN
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_exception.opp):
    """Test base exception is handled."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "smart_meter_texas.Client.authenticate",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_LOGIN,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_form_duplicate_account.opp):
    """Test that a duplicate account cannot be configured."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="user123",
        data={"username": "user123", "password": "password123"},
    ).add_to_opp(opp)

    with patch(
        "smart_meter_texas.Client.authenticate",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"username": "user123", "password": "password123"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
