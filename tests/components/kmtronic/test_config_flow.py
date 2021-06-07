"""Test the kmtronic config flow."""
from unittest.mock import Mock, patch

from aiohttp import ClientConnectorError, ClientResponseError

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.kmtronic.const import CONF_REVERSE, DOMAIN
from openpeerpower.config_entries import ConfigEntryState

from tests.common import MockConfigEntry


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.kmtronic.config_flow.KMTronicHubAPI.async_get_status",
        return_value=[Mock()],
    ), patch(
        "openpeerpower.components.kmtronic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "1.1.1.1"
    assert result2["data"] == {
        "host": "1.1.1.1",
        "username": "test-username",
        "password": "test-password",
    }
    await opp.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_options(opp, aioclient_mock):
    """Test that the options form."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "1.1.1.1",
            "username": "admin",
            "password": "admin",
        },
    )
    config_entry.add_to_opp(opp)

    aioclient_mock.get(
        "http://1.1.1.1/status.xml",
        text="<response><relay0>0</relay0><relay1>0</relay1></response>",
    )
    await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    result = await opp.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_REVERSE: True}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert config_entry.options == {CONF_REVERSE: True}

    await opp.async_block_till_done()

    assert config_entry.state == config_entries.ConfigEntryState.LOADED


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.kmtronic.config_flow.KMTronicHubAPI.async_get_status",
        side_effect=ClientResponseError(None, None, status=401),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.kmtronic.config_flow.KMTronicHubAPI.async_get_status",
        side_effect=ClientConnectorError(None, Mock()),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(opp):
    """Test we handle unknown errors."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.kmtronic.config_flow.KMTronicHubAPI.async_get_status",
        side_effect=Exception(),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}
