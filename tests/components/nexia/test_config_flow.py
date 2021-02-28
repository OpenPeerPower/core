"""Test the nexia config flow."""
from unittest.mock import MagicMock, patch

from requests.exceptions import ConnectTimeout, HTTPError

from openpeerpower import config_entries, setup
from openpeerpower.components.nexia.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.nexia.config_flow.NexiaHome.get_name",
        return_value="myhouse",
    ), patch(
        "openpeerpower.components.nexia.config_flow.NexiaHome.login",
        side_effect=MagicMock(),
    ), patch(
        "openpeerpower.components.nexia.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.nexia.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "myhouse"
    assert result2["data"] == {
        CONF_USERNAME: "username",
        CONF_PASSWORD: "password",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("openpeerpower.components.nexia.config_flow.NexiaHome.login"):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nexia.config_flow.NexiaHome.login",
        side_effect=ConnectTimeout,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth_http_401.opp):
    """Test we handle invalid auth error from http 401."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    response_mock = MagicMock()
    type(response_mock).status_code = 401
    with patch(
        "openpeerpower.components.nexia.config_flow.NexiaHome.login",
        side_effect=HTTPError(response=response_mock),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect_not_found(opp):
    """Test we handle cannot connect from an http not found error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    response_mock = MagicMock()
    type(response_mock).status_code = 404
    with patch(
        "openpeerpower.components.nexia.config_flow.NexiaHome.login",
        side_effect=HTTPError(response=response_mock),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_broad_exception(opp):
    """Test we handle invalid auth error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nexia.config_flow.NexiaHome.login",
        side_effect=ValueError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}
