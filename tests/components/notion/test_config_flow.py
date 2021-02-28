"""Define tests for the Notion config flow."""
from unittest.mock import AsyncMock, patch

import aionotion
import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.notion import DOMAIN, config_flow
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


@pytest.fixture
def mock_client():
    """Define a fixture for a client creation coroutine."""
    return AsyncMock(return_value=None)


@pytest.fixture
def mock_aionotion(mock_client):
    """Mock the aionotion library."""
    with patch("openpeerpower.components.notion.config_flow.async_get_client") as mock_:
        mock_.side_effect = mock_client
        yield mock_


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    conf = {CONF_USERNAME: "user@host.com", CONF_PASSWORD: "password123"}

    MockConfigEntry(domain=DOMAIN, unique_id="user@host.com", data=conf).add_to_opp(
        opp
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "mock_client", [AsyncMock(side_effect=aionotion.errors.NotionError)]
)
async def test_invalid_credentials(opp, mock_aionotion):
    """Test that an invalid API/App Key throws an error."""
    conf = {CONF_USERNAME: "user@host.com", CONF_PASSWORD: "password123"}

    flow = config_flow.NotionFlowHandler()
    flow.opp = opp
    flow.context = {"source": SOURCE_USER}

    result = await flow.async_step_user(user_input=conf)
    assert result["errors"] == {"base": "invalid_auth"}


async def test_show_form(opp):
    """Test that the form is served with no input."""
    flow = config_flow.NotionFlowHandler()
    flow.opp = opp
    flow.context = {"source": SOURCE_USER}

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_step_user(opp, mock_aionotion):
    """Test that the user step works."""
    conf = {CONF_USERNAME: "user@host.com", CONF_PASSWORD: "password123"}

    flow = config_flow.NotionFlowHandler()
    flow.opp = opp
    flow.context = {"source": SOURCE_USER}

    result = await flow.async_step_user(user_input=conf)
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "user@host.com"
    assert result["data"] == {
        CONF_USERNAME: "user@host.com",
        CONF_PASSWORD: "password123",
    }
