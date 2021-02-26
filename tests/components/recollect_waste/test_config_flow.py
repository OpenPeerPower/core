"""Define tests for the ReCollect Waste config flow."""
from unittest.mock import patch

from aiorecollect.errors import RecollectError

from openpeerpower import data_entry_flow
from openpeerpower.components.recollect_waste import (
    CONF_PLACE_ID,
    CONF_SERVICE_ID,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_FRIENDLY_NAME

from tests.common import MockConfigEntry


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    conf = {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}

    MockConfigEntry(domain=DOMAIN, unique_id="12345, 12345", data=conf).add_to(opp(
        opp
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_place_or_service_id(opp):
    """Test that an invalid Place or Service ID throws an error."""
    conf = {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}

    with patch(
        "aiorecollect.client.Client.async_get_next_pickup_event",
        side_effect=RecollectError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "invalid_place_or_service_id"}


async def test_options_flow(opp):
    """Test config flow options."""
    conf = {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}

    config_entry = MockConfigEntry(domain=DOMAIN, unique_id="12345, 12345", data=conf)
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.recollect_waste.async_setup_entry", return_value=True
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        result = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_FRIENDLY_NAME: True}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options == {CONF_FRIENDLY_NAME: True}


async def test_show_form(opp):
    """Test that the form is served with no input."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_import(opp):
    """Test that the user step works."""
    conf = {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}

    with patch(
        "openpeerpower.components.recollect_waste.async_setup_entry", return_value=True
    ), patch(
        "aiorecollect.client.Client.async_get_next_pickup_event", return_value=True
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
        )
        await opp.async_block_till_done()
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "12345, 12345"
        assert result["data"] == {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}


async def test_step_user(opp):
    """Test that the user step works."""
    conf = {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}

    with patch(
        "openpeerpower.components.recollect_waste.async_setup_entry", return_value=True
    ), patch(
        "aiorecollect.client.Client.async_get_next_pickup_event", return_value=True
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        await opp.async_block_till_done()
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "12345, 12345"
        assert result["data"] == {CONF_PLACE_ID: "12345", CONF_SERVICE_ID: "12345"}
