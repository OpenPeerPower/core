"""Test the Coronavirus config flow."""
from unittest.mock import MagicMock, patch

from aiohttp import ClientError

from openpeerpower import config_entries, setup
from openpeerpower.components.coronavirus.const import DOMAIN, OPTION_WORLDWIDE
from openpeerpower.core import OpenPeerPower


async def test_form(opp: OpenPeerPower) -> None:
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"country": OPTION_WORLDWIDE},
    )
    assert result2["type"] == "create_entry"
    assert result2["title"] == "Worldwide"
    assert result2["result"].unique_id == OPTION_WORLDWIDE
    assert result2["data"] == {
        "country": OPTION_WORLDWIDE,
    }
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 4


@patch(
    "coronavirus.get_cases",
    side_effect=ClientError,
)
async def test_abort_on_connection_error(
    mock_get_cases: MagicMock, opp: OpenPeerPower
) -> None:
    """Test we abort on connection error."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert "type" in result
    assert result["type"] == "abort"
    assert "reason" in result
    assert result["reason"] == "cannot_connect"
