"""Test the habitica config flow."""
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientResponseError

from openpeerpower import config_entries, setup
from openpeerpower.components.habitica.const import DEFAULT_URL, DOMAIN

from tests.common import MockConfigEntry


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_obj = MagicMock()
    mock_obj.user.get = AsyncMock()

    with patch(
        "openpeerpower.components.habitica.config_flow.HabitipyAsync",
        return_value=mock_obj,
    ), patch(
        "openpeerpower.components.habitica.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.habitica.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_user": "test-api-user", "api_key": "test-api-key"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Default username"
    assert result2["data"] == {
        "url": DEFAULT_URL,
        "api_user": "test-api-user",
        "api_key": "test-api-key",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_credentials(opp):
    """Test we handle invalid credentials error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_obj = MagicMock()
    mock_obj.user.get = AsyncMock(side_effect=ClientResponseError(MagicMock(), ()))

    with patch(
        "openpeerpower.components.habitica.config_flow.HabitipyAsync",
        return_value=mock_obj,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": DEFAULT_URL,
                "api_user": "test-api-user",
                "api_key": "test-api-key",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_credentials"}


async def test_form_unexpected_exception(opp):
    """Test we handle unexpected exception error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_obj = MagicMock()
    mock_obj.user.get = AsyncMock(side_effect=Exception)

    with patch(
        "openpeerpower.components.habitica.config_flow.HabitipyAsync",
        return_value=mock_obj,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": DEFAULT_URL,
                "api_user": "test-api-user",
                "api_key": "test-api-key",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_manual_flow_config_exist(opp):
    """Test config flow discovers only already configured config."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-api-user",
        data={"api_user": "test-api-user", "api_key": "test-api-key"},
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_obj = MagicMock()
    mock_obj.user.get = AsyncMock(return_value={"api_user": "test-api-user"})

    with patch(
        "openpeerpower.components.habitica.config_flow.HabitipyAsync",
        return_value=mock_obj,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": DEFAULT_URL,
                "api_user": "test-api-user",
                "api_key": "test-api-key",
            },
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
