"""Tests for the Freebox config flow."""
from unittest.mock import Mock, patch

from freebox_api.exceptions import (
    AuthorizationError,
    HttpRequestError,
    InvalidTokenError,
)

from openpeerpower import data_entry_flow
from openpeerpower.components.freebox.const import DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER, SOURCE_ZEROCONF
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower

from .const import MOCK_HOST, MOCK_PORT

from tests.common import MockConfigEntry

MOCK_ZEROCONF_DATA = {
    "host": "192.168.0.254",
    "port": 80,
    "hostname": "Freebox-Server.local.",
    "type": "_fbx-api._tcp.local.",
    "name": "Freebox Server._fbx-api._tcp.local.",
    "properties": {
        "api_version": "8.0",
        "device_type": "FreeboxServer1,2",
        "api_base_url": "/api/",
        "uid": "b15ab20debb399f95001a9ca207d2777",
        "https_available": "1",
        "https_port": f"{MOCK_PORT}",
        "box_model": "fbxgw-r2/full",
        "box_model_name": "Freebox Server (r2)",
        "api_domain": MOCK_HOST,
    },
}


async def test_user(opp: OpenPeerPower):
    """Test user config."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # test with all provided
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "link"


async def test_import(opp: OpenPeerPower):
    """Test import step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "link"


async def test_zeroconf(opp: OpenPeerPower):
    """Test zeroconf step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "link"


async def test_link(opp: OpenPeerPower, router: Mock):
    """Test linking."""
    with patch(
        "openpeerpower.components.freebox.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.freebox.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
        )

        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["result"].unique_id == MOCK_HOST
        assert result["title"] == MOCK_HOST
        assert result["data"][CONF_HOST] == MOCK_HOST
        assert result["data"][CONF_PORT] == MOCK_PORT

        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_abort_if_already_setup(opp: OpenPeerPower):
    """Test we abort if component is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
        unique_id=MOCK_HOST,
    ).add_to_opp(opp)

    # Should fail, same MOCK_HOST (import)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same MOCK_HOST (flow)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_on_link_failed(opp: OpenPeerPower):
    """Test when we have errors during linking the router."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: MOCK_HOST, CONF_PORT: MOCK_PORT},
    )

    with patch(
        "openpeerpower.components.freebox.router.Freepybox.open",
        side_effect=AuthorizationError(),
    ):
        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "register_failed"}

    with patch(
        "openpeerpower.components.freebox.router.Freepybox.open",
        side_effect=HttpRequestError(),
    ):
        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "cannot_connect"}

    with patch(
        "openpeerpower.components.freebox.router.Freepybox.open",
        side_effect=InvalidTokenError(),
    ):
        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "unknown"}
