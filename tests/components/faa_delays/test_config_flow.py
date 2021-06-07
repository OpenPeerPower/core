"""Test the FAA Delays config flow."""
from unittest.mock import patch

from aiohttp import ClientConnectionError
import faadelays

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.faa_delays.const import DOMAIN
from openpeerpower.const import CONF_ID
from openpeerpower.exceptions import OpenPeerPowerError

from tests.common import MockConfigEntry


async def mock_valid_airport(self, *args, **kwargs):
    """Return a valid airport."""
    self.name = "Test airport"


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch.object(faadelays.Airport, "update", new=mock_valid_airport), patch(
        "openpeerpower.components.faa_delays.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Test airport"
    assert result2["data"] == {
        "id": "test",
    }
    await opp.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1


async def test_duplicate_error(opp):
    """Test that we handle a duplicate configuration."""
    conf = {CONF_ID: "test"}

    MockConfigEntry(domain=DOMAIN, unique_id="test", data=conf).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_form_invalid_airport(opp):
    """Test we handle invalid airport."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "faadelays.Airport.update",
        side_effect=faadelays.InvalidAirport,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {CONF_ID: "invalid_airport"}


async def test_form_cannot_connect(opp):
    """Test we handle a connection error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("faadelays.Airport.update", side_effect=ClientConnectionError):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unexpected_exception(opp):
    """Test we handle an unexpected exception."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("faadelays.Airport.update", side_effect=OpenPeerPowerError):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}
