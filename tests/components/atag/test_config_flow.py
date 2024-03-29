"""Tests for the Atag config flow."""
from unittest.mock import PropertyMock, patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.atag import DOMAIN
from openpeerpower.core import OpenPeerPower

from . import UID, USER_INPUT, init_integration, mock_connection

from tests.test_util.aiohttp import AiohttpClientMocker


async def test_show_form(opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker):
    """Test that the form is served with no input."""
    mock_connection(aioclient_mock)
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_adding_second_device(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that only one Atag configuration is allowed."""
    await init_integration(opp, aioclient_mock)
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    with patch(
        "pyatag.AtagOne.id",
        new_callable=PropertyMock(return_value="secondary_device"),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_connection_error(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
):
    """Test we show user form on Atag connection error."""
    mock_connection(aioclient_mock, conn_error=True)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unauthorized(opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker):
    """Test we show correct form when Unauthorized error is raised."""
    mock_connection(aioclient_mock, authorized=False)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unauthorized"}


async def test_full_flow_implementation(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test registering an integration and finishing flow works."""
    mock_connection(aioclient_mock)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == UID
    assert result["result"].unique_id == UID
