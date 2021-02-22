"""Tests for the Twente Milieu config flow."""
import aiohttp

from openpeerpower import data_entry_flow
from openpeerpower.components.twentemilieu import config_flow
from openpeerpower.components.twentemilieu.const import (
    CONF_HOUSE_LETTER,
    CONF_HOUSE_NUMBER,
    CONF_POST_CODE,
    DOMAIN,
)
from openpeerpower.const import CONF_ID, CONTENT_TYPE_JSON

from tests.common import MockConfigEntry

FIXTURE_USER_INPUT = {
    CONF_ID: "12345",
    CONF_POST_CODE: "1234AB",
    CONF_HOUSE_NUMBER: "1",
    CONF_HOUSE_LETTER: "A",
}


async def test_show_set_form.opp):
    """Test that the setup form is served."""
    flow = config_flow.TwenteMilieuFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_connection_error(opp, aioclient_mock):
    """Test we show user form on Twente Milieu connection error."""
    aioclient_mock.post(
        "https://twentemilieuapi.ximmio.com/api/FetchAdress", exc=aiohttp.ClientError
    )

    flow = config_flow.TwenteMilieuFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=FIXTURE_USER_INPUT)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_invalid_address.opp, aioclient_mock):
    """Test we show user form on Twente Milieu invalid address error."""
    aioclient_mock.post(
        "https://twentemilieuapi.ximmio.com/api/FetchAdress",
        json={"dataList": []},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    flow = config_flow.TwenteMilieuFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=FIXTURE_USER_INPUT)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_address"}


async def test_address_already_set_up.opp, aioclient_mock):
    """Test we abort if address has already been set up."""
    MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT, title="12345").add_to.opp(
        opp
    )

    aioclient_mock.post(
        "https://twentemilieuapi.ximmio.com/api/FetchAdress",
        json={"dataList": [{"UniqueId": "12345"}]},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    flow = config_flow.TwenteMilieuFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=FIXTURE_USER_INPUT)

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_full_flow_implementation.opp, aioclient_mock):
    """Test registering an integration and finishing flow works."""
    aioclient_mock.post(
        "https://twentemilieuapi.ximmio.com/api/FetchAdress",
        json={"dataList": [{"UniqueId": "12345"}]},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    flow = config_flow.TwenteMilieuFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user(user_input=FIXTURE_USER_INPUT)
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "12345"
    assert result["data"][CONF_POST_CODE] == FIXTURE_USER_INPUT[CONF_POST_CODE]
    assert result["data"][CONF_HOUSE_NUMBER] == FIXTURE_USER_INPUT[CONF_HOUSE_NUMBER]
    assert result["data"][CONF_HOUSE_LETTER] == FIXTURE_USER_INPUT[CONF_HOUSE_LETTER]
