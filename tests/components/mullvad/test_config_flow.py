"""Test the Mullvad config flow."""
from unittest.mock import patch

from mullvad_api import MullvadAPIError

from openpeerpower import config_entries, setup
from openpeerpower.components.mullvad.const import DOMAIN
from openpeerpower.data_entry_flow import RESULT_TYPE_ABORT, RESULT_TYPE_FORM

from tests.common import MockConfigEntry


async def test_form_user(opp):
    """Test we can setup by the user."""
    await setup.async_setup_component(opp, DOMAIN, {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert not result["errors"]

    with patch(
        "openpeerpower.components.mullvad.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.mullvad.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.mullvad.config_flow.MullvadAPI"
    ) as mock_mullvad_api:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Mullvad VPN"
    assert result2["data"] == {}
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_mullvad_api.mock_calls) == 1


async def test_form_user_only_once(opp):
    """Test we can setup by the user only once."""
    MockConfigEntry(domain=DOMAIN).add_to_opp(opp)
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_connection_error(opp):
    """Test we show an error when we have trouble connecting."""
    await setup.async_setup_component(opp, DOMAIN, {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.mullvad.config_flow.MullvadAPI",
        side_effect=MullvadAPIError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_unknown_error(opp):
    """Test we show an error when an unknown error occurs."""
    await setup.async_setup_component(opp, DOMAIN, {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.mullvad.config_flow.MullvadAPI",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}
