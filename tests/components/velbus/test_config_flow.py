"""Tests for the Velbus config flow."""
from unittest.mock import Mock, patch

import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.velbus import config_flow
from openpeerpower.const import CONF_NAME, CONF_PORT

from tests.common import MockConfigEntry

PORT_SERIAL = "/dev/ttyACME100"
PORT_TCP = "127.0.1.0.1:3788"


@pytest.fixture(name="controller_assert")
def mock_controller_assert():
    """Mock the velbus controller with an assert."""
    with patch("velbus.Controller", side_effect=Exception()):
        yield


@pytest.fixture(name="controller")
def mock_controller():
    """Mock a successful velbus controller."""
    controller = Mock()
    with patch("velbus.Controller", return_value=controller):
        yield controller


def init_config_flow.opp):
    """Init a configuration flow."""
    flow = config_flow.VelbusConfigFlow()
    flow.opp = opp
    return flow


async def test_user.opp, controller):
    """Test user config."""
    flow = init_config_flow.opp)

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user(
        {CONF_NAME: "Velbus Test Serial", CONF_PORT: PORT_SERIAL}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "velbus_test_serial"
    assert result["data"][CONF_PORT] == PORT_SERIAL

    result = await flow.async_step_user(
        {CONF_NAME: "Velbus Test TCP", CONF_PORT: PORT_TCP}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "velbus_test_tcp"
    assert result["data"][CONF_PORT] == PORT_TCP


async def test_user_fail.opp, controller_assert):
    """Test user config."""
    flow = init_config_flow.opp)

    result = await flow.async_step_user(
        {CONF_NAME: "Velbus Test Serial", CONF_PORT: PORT_SERIAL}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_PORT: "cannot_connect"}

    result = await flow.async_step_user(
        {CONF_NAME: "Velbus Test TCP", CONF_PORT: PORT_TCP}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_PORT: "cannot_connect"}


async def test_import.opp, controller):
    """Test import step."""
    flow = init_config_flow.opp)

    result = await flow.async_step_import({CONF_PORT: PORT_TCP})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "velbus_import"


async def test_abort_if_already_setup_opp):
    """Test we abort if Daikin is already setup."""
    flow = init_config_flow.opp)
    MockConfigEntry(
        domain="velbus", data={CONF_PORT: PORT_TCP, CONF_NAME: "velbus home"}
    ).add_to.opp.opp)

    result = await flow.async_step_import(
        {CONF_PORT: PORT_TCP, CONF_NAME: "velbus import test"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    result = await flow.async_step_user(
        {CONF_PORT: PORT_TCP, CONF_NAME: "velbus import test"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"port": "already_configured"}
