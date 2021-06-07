"""Test the MyQ config flow."""
from unittest.mock import patch

from pymyq.errors import InvalidCredentialsError, MyQError

from openpeerpower import config_entries, setup
from openpeerpower.components.myq.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


async def test_form_user(opp):
    """Test we get the user form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        return_value=True,
    ), patch(
        "openpeerpower.components.myq.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "test-username"
    assert result2["data"] == {
        "username": "test-username",
        "password": "test-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        side_effect=InvalidCredentialsError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"password": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        side_effect=MyQError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_exception(opp):
    """Test we handle unknown exceptions."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_reauth(opp):
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@test.org",
            CONF_PASSWORD: "secret",
        },
        unique_id="test@test.org",
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "unique_id": "test@test.org"},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        side_effect=InvalidCredentialsError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"password": "invalid_auth"}

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        side_effect=MyQError,
    ):
        result3 = await opp.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_PASSWORD: "test-password",
            },
        )

    assert result3["type"] == "form"
    assert result3["errors"] == {"base": "cannot_connect"}

    with patch(
        "openpeerpower.components.myq.config_flow.pymyq.login",
        return_value=True,
    ), patch(
        "openpeerpower.components.myq.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await opp.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_PASSWORD: "test-password",
            },
        )

    assert mock_setup_entry.called
    assert result4["type"] == "abort"
    assert result4["reason"] == "reauth_successful"
