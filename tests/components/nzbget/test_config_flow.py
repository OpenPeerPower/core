"""Test the NZBGet config flow."""
from unittest.mock import patch

from pynzbgetapi import NZBGetAPIException

from openpeerpower.components.nzbget.const import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_SCAN_INTERVAL, CONF_VERIFY_SSL
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)
from openpeerpower.setup import async_setup_component

from . import (
    ENTRY_CONFIG,
    USER_INPUT,
    _patch_async_setup,
    _patch_async_setup_entry,
    _patch_history,
    _patch_status,
    _patch_version,
)

from tests.common import MockConfigEntry


async def test_user_form.opp):
    """Test we get the user initiated form."""
    await async_setup_component.opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with _patch_version(), _patch_status(), _patch_history(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "10.10.10.30"
    assert result["data"] == {**USER_INPUT, CONF_VERIFY_SSL: False}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_show_advanced_options.opp):
    """Test we get the user initiated form with advanced options shown."""
    await async_setup_component.opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER, "show_advanced_options": True}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    user_input_advanced = {
        **USER_INPUT,
        CONF_VERIFY_SSL: True,
    }

    with _patch_version(), _patch_status(), _patch_history(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input_advanced,
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "10.10.10.30"
    assert result["data"] == {**USER_INPUT, CONF_VERIFY_SSL: True}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nzbget.coordinator.NZBGetAPI.version",
        side_effect=NZBGetAPIException(),
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_form_unexpected_exception.opp):
    """Test we handle unexpected exception."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nzbget.coordinator.NZBGetAPI.version",
        side_effect=Exception(),
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "unknown"


async def test_user_form_single_instance_allowed.opp):
    """Test that configuring more than one instance is rejected."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow.opp, nzbget_api):
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_CONFIG,
        options={CONF_SCAN_INTERVAL: 5},
    )
    entry.add_to.opp.opp)

    with patch("openpeerpower.components.nzbget.PLATFORMS", []):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert entry.options[CONF_SCAN_INTERVAL] == 5

    result = await opp.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    with _patch_async_setup(), _patch_async_setup_entry():
        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_SCAN_INTERVAL: 15},
        )
        await opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"][CONF_SCAN_INTERVAL] == 15
