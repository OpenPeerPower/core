"""Test the Aurora config flow."""

from unittest.mock import patch

from aiohttp import ClientError

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.aurora.const import DOMAIN

from tests.common import MockConfigEntry

DATA = {
    "name": "Home",
    "latitude": -10,
    "longitude": 10.2,
}


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.aurora.config_flow.AuroraForecast.get_forecast_data",
        return_value=True,
    ), patch(
        "openpeerpower.components.aurora.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.aurora.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Aurora - Home"
    assert result2["data"] == DATA
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect.opp):
    """Test if invalid response or no connection returned from the API."""

    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.aurora.AuroraForecast.get_forecast_data",
        side_effect=ClientError,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_with_unknown_error.opp):
    """Test with unknown error response from the API."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.aurora.AuroraForecast.get_forecast_data",
        side_effect=Exception,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown"}


async def test_option_flow.opp):
    """Test option flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_opp.opp)

    assert not entry.options

    with patch("openpeerpower.components.aurora.async_setup_entry", return_value=True):
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        result = await.opp.config_entries.options.async_init(
            entry.entry_id,
            data=None,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await.opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"forecast_threshold": 65},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"]["forecast_threshold"] == 65
