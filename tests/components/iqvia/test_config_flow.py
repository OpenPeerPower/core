"""Define tests for the IQVIA config flow."""
from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.iqvia import CONF_ZIP_CODE, DOMAIN
from openpeerpower.config_entries import SOURCE_USER

from tests.common import MockConfigEntry


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    conf = {CONF_ZIP_CODE: "12345"}

    MockConfigEntry(domain=DOMAIN, unique_id="12345", data=conf).add_to.opp.opp)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_zip_code.opp):
    """Test that an invalid ZIP code key throws an error."""
    conf = {CONF_ZIP_CODE: "abcde"}

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_ZIP_CODE: "invalid_zip_code"}


async def test_show_form.opp):
    """Test that the form is served with no input."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_user.opp):
    """Test that the user step works (without MFA)."""
    conf = {CONF_ZIP_CODE: "12345"}

    with patch("openpeerpower.components.iqvia.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "12345"
        assert result["data"] == {CONF_ZIP_CODE: "12345"}
