"""Test the Flick Electric config flow."""
import asyncio
from unittest.mock import patch

from pyflick.authentication import AuthException

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.flick_electric.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

CONF = {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"}


async def _flow_submit.opp):
    return await opp..config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=CONF,
    )


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.flick_electric.config_flow.SimpleFlickAuth.async_get_access_token",
        return_value="123456789abcdef",
    ), patch(
        "openpeerpower.components.flick_electric.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.flick_electric.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            CONF,
        )
        await opp..async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "Flick Electric: test-username"
    assert result2["data"] == CONF
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_duplicate_login.opp):
    """Test uniqueness of username."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONF,
        title="Flick Electric: test-username",
        unique_id="flick_electric_test-username",
    )
    entry.add_to_opp.opp)

    with patch(
        "openpeerpower.components.flick_electric.config_flow.SimpleFlickAuth.async_get_access_token",
        return_value="123456789abcdef",
    ):
        result = await _flow_submit.opp)

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    with patch(
        "openpeerpower.components.flick_electric.config_flow.SimpleFlickAuth.async_get_access_token",
        side_effect=AuthException,
    ):
        result = await _flow_submit.opp)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    with patch(
        "openpeerpower.components.flick_electric.config_flow.SimpleFlickAuth.async_get_access_token",
        side_effect=asyncio.TimeoutError,
    ):
        result = await _flow_submit.opp)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_generic_exception.opp):
    """Test we handle cannot connect error."""
    with patch(
        "openpeerpower.components.flick_electric.config_flow.SimpleFlickAuth.async_get_access_token",
        side_effect=Exception,
    ):
        result = await _flow_submit.opp)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "unknown"}
