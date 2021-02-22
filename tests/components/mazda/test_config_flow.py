"""Test the Mazda Connected Services config flow."""
from unittest.mock import patch

import aiohttp

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.mazda.config_flow import (
    MazdaAccountLockedException,
    MazdaAuthenticationException,
)
from openpeerpower.components.mazda.const import DOMAIN
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry

FIXTURE_USER_INPUT = {
    CONF_EMAIL: "example@example.com",
    CONF_PASSWORD: "password",
    CONF_REGION: "MNAO",
}
FIXTURE_USER_INPUT_REAUTH = {
    CONF_EMAIL: "example@example.com",
    CONF_PASSWORD: "password_fixed",
    CONF_REGION: "MNAO",
}


async def test_form.opp):
    """Test the entire flow."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch(
        "openpeerpower.components.mazda.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await.opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == FIXTURE_USER_INPUT[CONF_EMAIL]
    assert result2["data"] == FIXTURE_USER_INPUT
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp: OpenPeerPower) -> None:
    """Test we handle invalid auth."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Failed to authenticate"),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await.opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_account_locked.opp: OpenPeerPower) -> None:
    """Test we handle account locked error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAccountLockedException("Account locked"),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await.opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "account_locked"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error.opp):
    """Test we handle unknown error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=Exception,
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_reauth_flow.opp: OpenPeerPower) -> None:
    """Test reauth works."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Failed to authenticate"),
    ):
        mock_config = MockConfigEntry(
            domain=DOMAIN,
            unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
            data=FIXTURE_USER_INPUT,
        )
        mock_config.add_to.opp.opp)

        await.opp.config_entries.async_setup(mock_config.entry_id)
        await.opp.async_block_till_done()

        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"
        assert result["errors"] == {"base": "invalid_auth"}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ):
        result2 = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth", "unique_id": FIXTURE_USER_INPUT[CONF_EMAIL]},
            data=FIXTURE_USER_INPUT_REAUTH,
        )
        await.opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result2["reason"] == "reauth_successful"


async def test_reauth_authorization_error.opp: OpenPeerPower) -> None:
    """Test we show user form on authorization error."""
    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Failed to authenticate"),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await.opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "invalid_auth"}


async def test_reauth_account_locked.opp: OpenPeerPower) -> None:
    """Test we show user form on account_locked error."""
    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAccountLockedException("Account locked"),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await.opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "account_locked"}


async def test_reauth_connection_error.opp: OpenPeerPower) -> None:
    """Test we show user form on connection error."""
    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=aiohttp.ClientError,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await.opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "cannot_connect"}


async def test_reauth_unknown_error.opp: OpenPeerPower) -> None:
    """Test we show user form on unknown error."""
    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=Exception,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await.opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "unknown"}


async def test_reauth_unique_id_not_found.opp: OpenPeerPower) -> None:
    """Test we show user form when unique id not found during reauth."""
    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        # Change the unique_id of the flow in order to cause a mismatch
        flows =.opp.config_entries.flow.async_progress()
        flows[0]["context"]["unique_id"] = "example2@example.com"

        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await.opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "unknown"}
