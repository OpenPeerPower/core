"""Tests for the Freebox config flow."""
from unittest.mock import AsyncMock, patch

from freebox_api.exceptions import (
    AuthorizationError,
    HttpRequestError,
    InvalidTokenError,
)
import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.freebox.const import DOMAIN
from openpeerpower.config_entries import SOURCE_DISCOVERY, SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_HOST, CONF_PORT

from tests.common import MockConfigEntry

HOST = "myrouter.freeboxos.fr"
PORT = 1234


@pytest.fixture(name="connect")
def mock_controller_connect():
    """Mock a successful connection."""
    with patch("openpeerpower.components.freebox.router.Freepybox") as service_mock:
        service_mock.return_value.open = AsyncMock()
        service_mock.return_value.system.get_config = AsyncMock(
            return_value={
                "mac": "abcd",
                "model_info": {"pretty_name": "Pretty Model"},
                "firmware_version": "123",
            }
        )
        service_mock.return_value.lan.get_hosts_list = AsyncMock()
        service_mock.return_value.connection.get_status = AsyncMock()
        service_mock.return_value.close = AsyncMock()
        yield service_mock


async def test_user.opp):
    """Test user config."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # test with all provided
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "link"


async def test_import.opp):
    """Test import step."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "link"


async def test_discovery.opp):
    """Test discovery step."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DISCOVERY},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "link"


async def test_link.opp, connect):
    """Test linking."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )

    result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == HOST
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT


async def test_abort_if_already_setup.opp):
    """Test we abort if component is already setup."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT}, unique_id=HOST
    ).add_to_opp.opp)

    # Should fail, same HOST (import)
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same HOST (flow)
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_on_link_failed.opp):
    """Test when we have errors during linking the router."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )

    with patch(
        "openpeerpower.components.freebox.router.Freepybox.open",
        side_effect=AuthorizationError(),
    ):
        result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "register_failed"}

    with patch(
        "openpeerpower.components.freebox.router.Freepybox.open",
        side_effect=HttpRequestError(),
    ):
        result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "cannot_connect"}

    with patch(
        "openpeerpower.components.freebox.router.Freepybox.open",
        side_effect=InvalidTokenError(),
    ):
        result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "unknown"}
