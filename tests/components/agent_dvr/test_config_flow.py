"""Tests for the Agent DVR config flow."""
from openpeerpower import data_entry_flow
from openpeerpower.components.agent_dvr import config_flow
from openpeerpower.components.agent_dvr.const import SERVER_URL
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_HOST, CONF_PORT, CONTENT_TYPE_JSON
from openpeerpowerr.core import OpenPeerPower

from . import init_integration

from tests.common import load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_show_user_form.opp: OpenPeerPower) -> None:
    """Test that the user set up form is served."""
    result = await opp..config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_user_device_exists_abort(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we abort flow if Agent device already configured."""
    await init_integration.opp, aioclient_mock)

    result = await opp..config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.local", CONF_PORT: 8090},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_connection_error.opp: OpenPeerPower, aioclient_mock) -> None:
    """Test we show user form on Agent connection error."""

    aioclient_mock.get("http://example.local:8090/command.cgi?cmd=getStatus", text="")

    result = await opp..config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.local", CONF_PORT: 8090},
    )

    assert result["errors"] == {"base": "cannot_connect"}
    assert result["step_id"] == "user"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_full_user_flow_implementation(
   .opp: OpenPeerPower, aioclient_mock
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.get(
        "http://example.local:8090/command.cgi?cmd=getStatus",
        text=load_fixture("agent_dvr/status.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        "http://example.local:8090/command.cgi?cmd=getObjects",
        text=load_fixture("agent_dvr/objects.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await opp..config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result = await opp..config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "example.local", CONF_PORT: 8090}
    )

    assert result["data"][CONF_HOST] == "example.local"
    assert result["data"][CONF_PORT] == 8090
    assert result["data"][SERVER_URL] == "http://example.local:8090/"
    assert result["title"] == "DESKTOP"
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

    entries = opp.config_entries.async_entries(config_flow.DOMAIN)
    assert entries[0].unique_id == "c0715bba-c2d0-48ef-9e3e-bc81c9ea4447"
