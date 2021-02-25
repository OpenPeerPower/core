"""Test the NuHeat config flow."""
from unittest.mock import MagicMock, patch

import requests

from openpeerpower import config_entries, setup
from openpeerpower.components.nuheat.const import CONF_SERIAL_NUMBER, DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME, HTTP_INTERNAL_SERVER_ERROR

from .mocks import _get_mock_thermostat_run


async def test_form_user.opp):
    """Test we get the form with user source."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_thermostat = _get_mock_thermostat_run()

    with patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.authenticate",
        return_value=True,
    ), patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.get_thermostat",
        return_value=mock_thermostat,
    ), patch(
        "openpeerpower.components.nuheat.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.nuheat.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_NUMBER: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Master bathroom"
    assert result2["data"] == {
        CONF_SERIAL_NUMBER: "12345",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.authenticate",
        side_effect=Exception,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_NUMBER: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}

    response_mock = MagicMock()
    type(response_mock).status_code = 401
    with patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.authenticate",
        side_effect=requests.HTTPError(response=response_mock),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_NUMBER: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_invalid_thermostat.opp):
    """Test we handle invalid thermostats."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    response_mock = MagicMock()
    type(response_mock).status_code = HTTP_INTERNAL_SERVER_ERROR

    with patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.authenticate",
        return_value=True,
    ), patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.get_thermostat",
        side_effect=requests.HTTPError(response=response_mock),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_NUMBER: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_thermostat"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nuheat.config_flow.nuheat.NuHeat.authenticate",
        side_effect=requests.exceptions.Timeout,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_SERIAL_NUMBER: "12345",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}
