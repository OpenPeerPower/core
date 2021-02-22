"""Tests for iAqualink config flow."""
from unittest.mock import patch

import iaqualink
import pytest

from openpeerpower.components.iaqualink import config_flow

from tests.common import MockConfigEntry, mock_coro

DATA = {"username": "test@example.com", "password": "pass"}


@pytest.mark.parametrize("step", ["import", "user"])
async def test_already_configured.opp, step):
    """Test config flow when iaqualink component is already setup."""
    MockConfigEntry(domain="iaqualink", data=DATA).add_to.opp.opp)

    flow = config_flow.AqualinkFlowHandler()
    flow.opp =.opp
    flow.context = {}

    fname = f"async_step_{step}"
    func = getattr(flow, fname)
    result = await func(DATA)

    assert result["type"] == "abort"


@pytest.mark.parametrize("step", ["import", "user"])
async def test_without_config(opp, step):
    """Test with no configuration."""
    flow = config_flow.AqualinkFlowHandler()
    flow.opp =.opp
    flow.context = {}

    fname = f"async_step_{step}"
    func = getattr(flow, fname)
    result = await func()

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}


@pytest.mark.parametrize("step", ["import", "user"])
async def test_with_invalid_credentials.opp, step):
    """Test config flow with invalid username and/or password."""
    flow = config_flow.AqualinkFlowHandler()
    flow.opp =.opp

    fname = f"async_step_{step}"
    func = getattr(flow, fname)
    with patch(
        "iaqualink.AqualinkClient.login", side_effect=iaqualink.AqualinkLoginException
    ):
        result = await func(DATA)

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.parametrize("step", ["import", "user"])
async def test_with_existing_config(opp, step):
    """Test with existing configuration."""
    flow = config_flow.AqualinkFlowHandler()
    flow.opp =.opp
    flow.context = {}

    fname = f"async_step_{step}"
    func = getattr(flow, fname)
    with patch("iaqualink.AqualinkClient.login", return_value=mock_coro(None)):
        result = await func(DATA)

    assert result["type"] == "create_entry"
    assert result["title"] == DATA["username"]
    assert result["data"] == DATA
