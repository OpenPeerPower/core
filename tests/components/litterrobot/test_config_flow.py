"""Test the Litter-Robot config flow."""
from unittest.mock import patch

from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException

from openpeerpower import config_entries, setup

from .common import CONF_USERNAME, CONFIG, DOMAIN


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.litterrobot.config_flow.LitterRobotHub.login",
        return_value=True,
    ), patch(
        "openpeerpower.components.litterrobot.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.litterrobot.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == CONFIG[DOMAIN][CONF_USERNAME]
    assert result2["data"] == CONFIG[DOMAIN]
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.litterrobot.config_flow.LitterRobotHub.login",
        side_effect=LitterRobotLoginException,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.litterrobot.config_flow.LitterRobotHub.login",
        side_effect=LitterRobotException,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(opp):
    """Test we handle unknown error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.litterrobot.config_flow.LitterRobotHub.login",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], CONFIG[DOMAIN]
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}
