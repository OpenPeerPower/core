"""Test the Canary config flow."""
from unittest.mock import patch

from requests import ConnectTimeout, HTTPError

from openpeerpower.components.canary.const import (
    CONF_FFMPEG_ARGUMENTS,
    DEFAULT_FFMPEG_ARGUMENTS,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_TIMEOUT
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)
from openpeerpower.setup import async_setup_component

from . import USER_INPUT, _patch_async_setup, _patch_async_setup_entry, init_integration


async def test_user_form(opp, canary_config_flow):
    """Test we get the user initiated form."""
    await async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "test-username"
    assert result["data"] == {**USER_INPUT, CONF_TIMEOUT: DEFAULT_TIMEOUT}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_cannot_connect(opp, canary_config_flow):
    """Test we handle errors that should trigger the cannot connect error."""
    canary_config_flow.side_effect = HTTPError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}

    canary_config_flow.side_effect = ConnectTimeout()

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_form_unexpected_exception(opp, canary_config_flow):
    """Test we handle unexpected exception."""
    canary_config_flow.side_effect = Exception()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "unknown"


async def test_user_form_single_instance_allowed(opp, canary_config_flow):
    """Test that configuring more than one instance is rejected."""
    await init_integration(opp, skip_entry_setup=True)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow(opp, canary):
    """Test updating options."""
    with patch("openpeerpower.components.canary.PLATFORMS", []):
        entry = await init_integration.opp)

    assert entry.options[CONF_FFMPEG_ARGUMENTS] == DEFAULT_FFMPEG_ARGUMENTS
    assert entry.options[CONF_TIMEOUT] == DEFAULT_TIMEOUT

    result = await opp.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    with _patch_async_setup(), _patch_async_setup_entry():
        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_FFMPEG_ARGUMENTS: "-v", CONF_TIMEOUT: 7},
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"][CONF_FFMPEG_ARGUMENTS] == "-v"
    assert result["data"][CONF_TIMEOUT] == 7
