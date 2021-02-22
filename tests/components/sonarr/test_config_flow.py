"""Test the Sonarr config flow."""
from unittest.mock import patch

from openpeerpower.components.sonarr.const import (
    CONF_UPCOMING_DAYS,
    CONF_WANTED_MAX_ITEMS,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_WANTED_MAX_ITEMS,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_REAUTH, SOURCE_USER
from openpeerpower.const import CONF_API_KEY, CONF_HOST, CONF_SOURCE, CONF_VERIFY_SSL
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from tests.components.sonarr import (
    HOST,
    MOCK_REAUTH_INPUT,
    MOCK_USER_INPUT,
    _patch_async_setup,
    _patch_async_setup_entry,
    mock_connection,
    mock_connection_error,
    mock_connection_invalid_auth,
    setup_integration,
)
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_show_user_form.opp: OpenPeerPowerType) -> None:
    """Test that the user set up form is served."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    assert result["step_id"] == "user"
    assert result["type"] == RESULT_TYPE_FORM


async def test_cannot_connect(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we show user form on connection error."""
    mock_connection_error(aioclient_mock)

    user_input = MOCK_USER_INPUT.copy()
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_invalid_auth(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we show user form on invalid auth."""
    mock_connection_invalid_auth(aioclient_mock)

    user_input = MOCK_USER_INPUT.copy()
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_unknown_error(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we show user form on unknown error."""
    user_input = MOCK_USER_INPUT.copy()
    with patch(
        "openpeerpower.components.sonarr.config_flow.Sonarr.update",
        side_effect=Exception,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
            data=user_input,
        )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "unknown"


async def test_full_reauth_flow_implementation(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the manual reauth flow from start to finish."""
    entry = await setup_integration.opp, aioclient_mock, skip_entry_setup=True)
    assert entry

    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_REAUTH},
        data={"config_entry_id": entry.entry_id, **entry.data},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = MOCK_REAUTH_INPUT.copy()
    with _patch_async_setup(), _patch_async_setup_entry() as mock_setup_entry:
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=user_input
        )
        await.opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "reauth_successful"

    assert entry.data[CONF_API_KEY] == "test-api-key-reauth"

    mock_setup_entry.assert_called_once()


async def test_full_user_flow_implementation(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full manual user flow from start to finish."""
    mock_connection(aioclient_mock)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = MOCK_USER_INPUT.copy()

    with _patch_async_setup(), _patch_async_setup_entry():
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST


async def test_full_user_flow_advanced_options(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full manual user flow with advanced options."""
    mock_connection(aioclient_mock)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER, "show_advanced_options": True}
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = {
        **MOCK_USER_INPUT,
        CONF_VERIFY_SSL: True,
    }

    with _patch_async_setup(), _patch_async_setup_entry():
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_VERIFY_SSL]


async def test_options_flow.opp, aioclient_mock: AiohttpClientMocker):
    """Test updating options."""
    with patch("openpeerpower.components.sonarr.PLATFORMS", []):
        entry = await setup_integration.opp, aioclient_mock)

    assert entry.options[CONF_UPCOMING_DAYS] == DEFAULT_UPCOMING_DAYS
    assert entry.options[CONF_WANTED_MAX_ITEMS] == DEFAULT_WANTED_MAX_ITEMS

    result = await.opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    with _patch_async_setup(), _patch_async_setup_entry():
        result = await.opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_UPCOMING_DAYS: 2, CONF_WANTED_MAX_ITEMS: 100},
        )
        await.opp.async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["data"][CONF_UPCOMING_DAYS] == 2
    assert result["data"][CONF_WANTED_MAX_ITEMS] == 100
