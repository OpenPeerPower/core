"""Tests for the Ambiclimate config flow."""
from unittest.mock import AsyncMock, patch

import ambiclimate

from openpeerpower import data_entry_flow
from openpeerpower.components.ambiclimate import config_flow
from openpeerpower.config import async_process_ha_core_config
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.setup import async_setup_component
from openpeerpower.util import aiohttp


async def init_config_flow.opp):
    """Init a configuration flow."""
    await async_process_ha_core_config(
       .opp,
        {"external_url": "https://example.com"},
    )
    await async_setup_component.opp, "http", {})

    config_flow.register_flow_implementation.opp, "id", "secret")
    flow = config_flow.AmbiclimateFlowHandler()

    flow.opp =.opp
    return flow


async def test_abort_if_no_implementation_registered.opp):
    """Test we abort if no implementation is registered."""
    flow = config_flow.AmbiclimateFlowHandler()
    flow.opp =.opp

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "missing_configuration"


async def test_abort_if_already_setup.opp):
    """Test we abort if Ambiclimate is already setup."""
    flow = await init_config_flow.opp)

    with patch.object.opp.config_entries, "async_entries", return_value=[{}]):
        result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    with patch.object.opp.config_entries, "async_entries", return_value=[{}]):
        result = await flow.async_step_code()
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_full_flow_implementation.opp):
    """Test registering an implementation and finishing flow works."""
    config_flow.register_flow_implementation.opp, None, None)
    flow = await init_config_flow.opp)

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "auth"
    assert (
        result["description_placeholders"]["cb_url"]
        == "https://example.com/api/ambiclimate"
    )

    url = result["description_placeholders"]["authorization_url"]
    assert "https://api.ambiclimate.com/oauth2/authorize" in url
    assert "client_id=id" in url
    assert "response_type=code" in url
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fapi%2Fambiclimate" in url

    with patch("ambiclimate.AmbiclimateOAuth.get_access_token", return_value="test"):
        result = await flow.async_step_code("123ABC")
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Ambiclimate"
    assert result["data"]["callback_url"] == "https://example.com/api/ambiclimate"
    assert result["data"][CONF_CLIENT_SECRET] == "secret"
    assert result["data"][CONF_CLIENT_ID] == "id"

    with patch("ambiclimate.AmbiclimateOAuth.get_access_token", return_value=None):
        result = await flow.async_step_code("123ABC")
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT

    with patch(
        "ambiclimate.AmbiclimateOAuth.get_access_token",
        side_effect=ambiclimate.AmbiclimateOauthError(),
    ):
        result = await flow.async_step_code("123ABC")
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_abort_invalid_code.opp):
    """Test if no code is given to step_code."""
    config_flow.register_flow_implementation.opp, None, None)
    flow = await init_config_flow.opp)

    with patch("ambiclimate.AmbiclimateOAuth.get_access_token", return_value=None):
        result = await flow.async_step_code("invalid")
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "access_token"


async def test_already_setup.opp):
    """Test when already setup."""
    config_flow.register_flow_implementation.opp, None, None)
    flow = await init_config_flow.opp)

    with patch.object.opp.config_entries, "async_entries", return_value=True):
        result = await flow.async_step_user()

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_view.opp):
    """Test view."""
   .opp.config_entries.flow.async_init = AsyncMock()

    request = aiohttp.MockRequest(
        b"", query_string="code=test_code", mock_source="test"
    )
    request.app = {.opp":.opp}
    view = config_flow.AmbiclimateAuthCallbackView()
    assert await view.get(request) == "OK!"

    request = aiohttp.MockRequest(b"", query_string="", mock_source="test")
    request.app = {.opp":.opp}
    view = config_flow.AmbiclimateAuthCallbackView()
    assert await view.get(request) == "No code"
