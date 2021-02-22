"""Test the Huisbaasje config flow."""
from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.huisbaasje.config_flow import (
    HuisbaasjeConnectionException,
    HuisbaasjeException,
)
from openpeerpower.components.huisbaasje.const import DOMAIN

from tests.common import MockConfigEntry


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "huisbaasje.Huisbaasje.authenticate", return_value=None
    ) as mock_authenticate, patch(
        "huisbaasje.Huisbaasje.get_user_id",
        return_value="test-id",
    ) as mock_get_user_id, patch(
        "openpeerpower.components.huisbaasje.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.huisbaasje.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        form_result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        await.opp.async_block_till_done()

    assert form_result["type"] == "create_entry"
    assert form_result["title"] == "test-username"
    assert form_result["data"] == {
        "id": "test-id",
        "username": "test-username",
        "password": "test-password",
    }
    assert len(mock_authenticate.mock_calls) == 1
    assert len(mock_get_user_id.mock_calls) == 1
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "huisbaasje.Huisbaasje.authenticate",
        side_effect=HuisbaasjeException,
    ):
        form_result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert form_result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert form_result["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "huisbaasje.Huisbaasje.authenticate",
        side_effect=HuisbaasjeConnectionException,
    ):
        form_result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert form_result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert form_result["errors"] == {"base": "connection_exception"}


async def test_form_unknown_error(opp):
    """Test we handle an unknown error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "huisbaasje.Huisbaasje.authenticate",
        side_effect=Exception,
    ):
        form_result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert form_result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert form_result["errors"] == {"base": "unknown"}


async def test_form_entry_exists(opp):
    """Test we handle an already existing entry."""
    MockConfigEntry(
        unique_id="test-id",
        domain=DOMAIN,
        data={
            "id": "test-id",
            "username": "test-username",
            "password": "test-password",
        },
        title="test-username",
    ).add_to.opp.opp)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("huisbaasje.Huisbaasje.authenticate", return_value=None), patch(
        "huisbaasje.Huisbaasje.get_user_id",
        return_value="test-id",
    ), patch(
        "openpeerpower.components.huisbaasje.async_setup", return_value=True
    ), patch(
        "openpeerpower.components.huisbaasje.async_setup_entry",
        return_value=True,
    ):
        form_result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert form_result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert form_result["reason"] == "already_configured"
