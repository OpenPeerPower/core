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
FIXTURE_USER_INPUT_REAUTH_CHANGED_EMAIL = {
    CONF_EMAIL: "example2@example.com",
    CONF_PASSWORD: "password_fixed",
    CONF_REGION: "MNAO",
}


async def test_form(opp):
    """Test the entire flow."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == FIXTURE_USER_INPUT[CONF_EMAIL]
    assert result2["data"] == FIXTURE_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1


async def test_account_already_exists(opp):
    """Test account already exists."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"


async def test_form_invalid_auth(opp: OpenPeerPower) -> None:
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Failed to authenticate"),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_account_locked(opp: OpenPeerPower) -> None:
    """Test we handle account locked error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAccountLockedException("Account locked"),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "account_locked"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(opp):
    """Test we handle unknown error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_reauth_flow(opp: OpenPeerPower) -> None:
    """Test reauth works."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Failed to authenticate"),
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ):
        await opp.config_entries.async_setup(mock_config.entry_id)
        await opp.async_block_till_done()

        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config.entry_id,
            },
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch("openpeerpower.components.mazda.async_setup_entry", return_value=True):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result2["reason"] == "reauth_successful"


async def test_reauth_authorization_error(opp: OpenPeerPower) -> None:
    """Test we show user form on authorization error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Failed to authenticate"),
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config.entry_id,
            },
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "invalid_auth"}


async def test_reauth_account_locked(opp: OpenPeerPower) -> None:
    """Test we show user form on account_locked error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=MazdaAccountLockedException("Account locked"),
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config.entry_id,
            },
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "account_locked"}


async def test_reauth_connection_error(opp: OpenPeerPower) -> None:
    """Test we show user form on connection error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=aiohttp.ClientError,
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config.entry_id,
            },
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "cannot_connect"}


async def test_reauth_unknown_error(opp: OpenPeerPower) -> None:
    """Test we show user form on unknown error."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        side_effect=Exception,
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config.entry_id,
            },
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "unknown"}


async def test_reauth_user_has_new_email_address(opp: OpenPeerPower) -> None:
    """Test reauth with a new email address but same account."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_EMAIL],
        data=FIXTURE_USER_INPUT,
    )
    mock_config.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch(
        "openpeerpower.components.mazda.async_setup_entry",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": mock_config.entry_id,
            },
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        # Change the email and ensure the entry and its unique id gets
        # updated in the event the user has changed their email with mazda
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT_REAUTH_CHANGED_EMAIL,
        )
        await opp.async_block_till_done()

        assert (
            mock_config.unique_id == FIXTURE_USER_INPUT_REAUTH_CHANGED_EMAIL[CONF_EMAIL]
        )
        assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result2["reason"] == "reauth_successful"
