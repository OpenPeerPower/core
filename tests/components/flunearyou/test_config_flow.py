"""Define tests for the flunearyou config flow."""
from unittest.mock import patch

from pyflunearyou.errors import FluNearYouError

from openpeerpower import data_entry_flow
from openpeerpower.components.flunearyou import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE

from tests.common import MockConfigEntry


async def test_duplicate_error.opp):
    """Test that an error is shown when duplicates are added."""
    conf = {CONF_LATITUDE: "51.528308", CONF_LONGITUDE: "-0.3817765"}

    MockConfigEntry(
        domain=DOMAIN, unique_id="51.528308, -0.3817765", data=conf
    ).add_to.opp.opp)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_general_error.opp):
    """Test that an error is shown on a library error."""
    conf = {CONF_LATITUDE: "51.528308", CONF_LONGITUDE: "-0.3817765"}

    with patch(
        "pyflunearyou.cdc.CdcReport.status_by_coordinates",
        side_effect=FluNearYouError,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["errors"] == {"base": "unknown"}


async def test_show_form.opp):
    """Test that the form is served with no input."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_user.opp):
    """Test that the user step works."""
    conf = {CONF_LATITUDE: "51.528308", CONF_LONGITUDE: "-0.3817765"}

    with patch(
        "openpeerpower.components.flunearyou.async_setup_entry", return_value=True
    ), patch("pyflunearyou.cdc.CdcReport.status_by_coordinates"):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "51.528308, -0.3817765"
        assert result["data"] == {
            CONF_LATITUDE: "51.528308",
            CONF_LONGITUDE: "-0.3817765",
        }
