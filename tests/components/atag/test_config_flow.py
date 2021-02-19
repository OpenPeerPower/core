"""Tests for the Atag config flow."""
from unittest.mock import PropertyMock, patch

from pyatag import errors

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.atag import DOMAIN
from openpeerpowerr.core import OpenPeerPower

from tests.components.atag import (
    PAIR_REPLY,
    RECEIVE_REPLY,
    UID,
    USER_INPUT,
    init_integration,
)
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_show_form.opp):
    """Test that the form is served with no input."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_adding_second_device(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that only one Atag configuration is allowed."""
    await init_integration.opp, aioclient_mock)
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
    with patch(
        "pyatag.AtagOne.id",
        new_callable=PropertyMock(return_value="secondary_device"),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_connection_error.opp):
    """Test we show user form on Atag connection error."""
    with patch("pyatag.AtagOne.authorize", side_effect=errors.AtagException()):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unauthorized.opp):
    """Test we show correct form when Unauthorized error is raised."""
    with patch("pyatag.AtagOne.authorize", side_effect=errors.Unauthorized()):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unauthorized"}


async def test_full_flow_implementation(
   .opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test registering an integration and finishing flow works."""
    aioclient_mock.post(
        "http://127.0.0.1:10000/pair",
        json=PAIR_REPLY,
    )
    aioclient_mock.post(
        "http://127.0.0.1:10000/retrieve",
        json=RECEIVE_REPLY,
    )
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == UID
    assert result["result"].unique_id == UID
