"""Tests for the Heos config flow module."""
from unittest.mock import patch
from urllib.parse import urlparse

from pyheos import HeosError

from openpeerpower import data_entry_flow
from openpeerpower.components import heos, ssdp
from openpeerpower.components.heos.config_flow import HeosFlowHandler
from openpeerpower.components.heos.const import DATA_DISCOVERED_HOSTS, DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_SSDP, SOURCE_USER
from openpeerpower.const import CONF_HOST


async def test_flow_aborts_already_setup(opp, config_entry):
    """Test flow aborts when entry already setup."""
    config_entry.add_to_opp(opp)
    flow = HeosFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_no_host_shows_form(opp):
    """Test form is shown when host not provided."""
    flow = HeosFlowHandler()
    flow.opp = opp
    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_cannot_connect_shows_error_form(opp, controller):
    """Test form is shown with error when cannot connect."""
    controller.connect.side_effect = HeosError()
    result = await opp.config_entries.flow.async_init(
        heos.DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "127.0.0.1"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"][CONF_HOST] == "cannot_connect"
    assert controller.connect.call_count == 1
    assert controller.disconnect.call_count == 1
    controller.connect.reset_mock()
    controller.disconnect.reset_mock()


async def test_create_entry_when_host_valid(opp, controller):
    """Test result type is create entry when host is valid."""
    data = {CONF_HOST: "127.0.0.1"}
    with patch("openpeerpower.components.heos.async_setup_entry", return_value=True):
        result = await opp.config_entries.flow.async_init(
            heos.DOMAIN, context={"source": SOURCE_USER}, data=data
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["result"].unique_id == DOMAIN
        assert result["title"] == "Controller (127.0.0.1)"
        assert result["data"] == data
        assert controller.connect.call_count == 1
        assert controller.disconnect.call_count == 1


async def test_create_entry_when_friendly_name_valid(opp, controller):
    """Test result type is create entry when friendly name is valid."""
    opp.data[DATA_DISCOVERED_HOSTS] = {"Office (127.0.0.1)": "127.0.0.1"}
    data = {CONF_HOST: "Office (127.0.0.1)"}
    with patch("openpeerpower.components.heos.async_setup_entry", return_value=True):
        result = await opp.config_entries.flow.async_init(
            heos.DOMAIN, context={"source": SOURCE_USER}, data=data
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["result"].unique_id == DOMAIN
        assert result["title"] == "Controller (127.0.0.1)"
        assert result["data"] == {CONF_HOST: "127.0.0.1"}
        assert controller.connect.call_count == 1
        assert controller.disconnect.call_count == 1
        assert DATA_DISCOVERED_HOSTS not in opp.data


async def test_discovery_shows_create_form(opp, controller, discovery_data):
    """Test discovery shows form to confirm setup and subsequent abort."""

    await opp.config_entries.flow.async_init(
        heos.DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_data
    )
    await opp.async_block_till_done()
    flows_in_progress = opp.config_entries.flow.async_progress()
    assert flows_in_progress[0]["context"]["unique_id"] == DOMAIN
    assert len(flows_in_progress) == 1
    assert opp.data[DATA_DISCOVERED_HOSTS] == {"Office (127.0.0.1)": "127.0.0.1"}

    port = urlparse(discovery_data[ssdp.ATTR_SSDP_LOCATION]).port
    discovery_data[ssdp.ATTR_SSDP_LOCATION] = f"http://127.0.0.2:{port}/"
    discovery_data[ssdp.ATTR_UPNP_FRIENDLY_NAME] = "Bedroom"

    await opp.config_entries.flow.async_init(
        heos.DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_data
    )
    await opp.async_block_till_done()
    flows_in_progress = opp.config_entries.flow.async_progress()
    assert flows_in_progress[0]["context"]["unique_id"] == DOMAIN
    assert len(flows_in_progress) == 1
    assert opp.data[DATA_DISCOVERED_HOSTS] == {
        "Office (127.0.0.1)": "127.0.0.1",
        "Bedroom (127.0.0.2)": "127.0.0.2",
    }


async def test_discovery_flow_aborts_already_setup(
    opp, controller, discovery_data, config_entry
):
    """Test discovery flow aborts when entry already setup."""
    config_entry.add_to_opp(opp)
    flow = HeosFlowHandler()
    flow.opp = opp
    result = await flow.async_step_ssdp(discovery_data)
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_discovery_sets_the_unique_id(opp, controller, discovery_data):
    """Test discovery sets the unique id."""

    port = urlparse(discovery_data[ssdp.ATTR_SSDP_LOCATION]).port
    discovery_data[ssdp.ATTR_SSDP_LOCATION] = f"http://127.0.0.2:{port}/"
    discovery_data[ssdp.ATTR_UPNP_FRIENDLY_NAME] = "Bedroom"

    await opp.config_entries.flow.async_init(
        heos.DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_data
    )
    await opp.async_block_till_done()
    flows_in_progress = opp.config_entries.flow.async_progress()
    assert flows_in_progress[0]["context"]["unique_id"] == DOMAIN
    assert len(flows_in_progress) == 1
    assert opp.data[DATA_DISCOVERED_HOSTS] == {"Bedroom (127.0.0.2)": "127.0.0.2"}


async def test_import_sets_the_unique_id(opp, controller):
    """Test import sets the unique id."""

    with patch("openpeerpower.components.heos.async_setup_entry", return_value=True):
        result = await opp.config_entries.flow.async_init(
            heos.DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_HOST: "127.0.0.2"},
        )
    await opp.async_block_till_done()
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == DOMAIN
