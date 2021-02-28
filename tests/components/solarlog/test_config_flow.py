"""Test the solarlog config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.solarlog import config_flow
from openpeerpower.components.solarlog.const import DEFAULT_HOST, DOMAIN
from openpeerpower.const import CONF_HOST, CONF_NAME

from tests.common import MockConfigEntry

NAME = "Solarlog test 1 2 3"
HOST = "http://1.1.1.1"


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.solarlog.config_flow.SolarLogConfigFlow._test_connection",
        return_value={"title": "solarlog test 1 2 3"},
    ), patch(
        "openpeerpower.components.solarlog.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.solarlog.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"], {"host": HOST, "name": NAME}
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "solarlog_test_1_2_3"
    assert result2["data"] == {"host": "http://1.1.1.1"}
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.fixture(name="test_connect")
def mock_controller():
    """Mock a successful _host_in_configuration_exists."""
    with patch(
        "openpeerpower.components.solarlog.config_flow.SolarLogConfigFlow._test_connection",
        return_value=True,
    ):
        yield


def init_config_flow(opp):
    """Init a configuration flow."""
    flow = config_flow.SolarLogConfigFlow()
    flow.opp = opp
    return flow


async def test_user(opp, test_connect):
    """Test user config."""
    flow = init_config_flow(opp)

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # tets with all provided
    result = await flow.async_step_user({CONF_NAME: NAME, CONF_HOST: HOST})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "solarlog_test_1_2_3"
    assert result["data"][CONF_HOST] == HOST


async def test_import(opp, test_connect):
    """Test import step."""
    flow = init_config_flow(opp)

    # import with only host
    result = await flow.async_step_import({CONF_HOST: HOST})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "solarlog"
    assert result["data"][CONF_HOST] == HOST

    # import with only name
    result = await flow.async_step_import({CONF_NAME: NAME})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "solarlog_test_1_2_3"
    assert result["data"][CONF_HOST] == DEFAULT_HOST

    # import with host and name
    result = await flow.async_step_import({CONF_HOST: HOST, CONF_NAME: NAME})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "solarlog_test_1_2_3"
    assert result["data"][CONF_HOST] == HOST


async def test_abort_if_already_setup_opp, test_connect):
    """Test we abort if the device is already setup."""
    flow = init_config_flow(opp)
    MockConfigEntry(
        domain="solarlog", data={CONF_NAME: NAME, CONF_HOST: HOST}
    ).add_to_opp(opp)

    # Should fail, same HOST different NAME (default)
    result = await flow.async_step_import(
        {CONF_HOST: HOST, CONF_NAME: "solarlog_test_7_8_9"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same HOST and NAME
    result = await flow.async_step_user({CONF_HOST: HOST, CONF_NAME: NAME})
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "already_configured"}

    # SHOULD pass, diff HOST (without http://), different NAME
    result = await flow.async_step_import(
        {CONF_HOST: "2.2.2.2", CONF_NAME: "solarlog_test_7_8_9"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "solarlog_test_7_8_9"
    assert result["data"][CONF_HOST] == "http://2.2.2.2"

    # SHOULD pass, diff HOST, same NAME
    result = await flow.async_step_import(
        {CONF_HOST: "http://2.2.2.2", CONF_NAME: NAME}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "solarlog_test_1_2_3"
    assert result["data"][CONF_HOST] == "http://2.2.2.2"
