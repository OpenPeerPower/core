"""Test the Nightscout config flow."""
from unittest.mock import patch

from aiohttp import ClientConnectionError, ClientResponseError

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.nightscout.const import DOMAIN
from openpeerpower.components.nightscout.utils import hash_from_url
from openpeerpower.const import CONF_URL

from tests.common import MockConfigEntry
from tests.components.nightscout import (
    GLUCOSE_READINGS,
    SERVER_STATUS,
    SERVER_STATUS_STATUS_ONLY,
)

CONFIG = {CONF_URL: "https://some.url:1234"}


async def test_form.opp):
    """Test we get the user initiated form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with _patch_glucose_readings(), _patch_server_status(), _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

        assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result2["title"] == SERVER_STATUS.name  # pylint: disable=maybe-no-member
        assert result2["data"] == CONFIG
        await.opp.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_server_status",
        side_effect=ClientConnectionError(),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "https://some.url:1234"},
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_user_form_api_key_required.opp):
    """Test we handle an unauthorized error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_server_status",
        return_value=SERVER_STATUS_STATUS_ONLY,
    ), patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_sgvs",
        side_effect=ClientResponseError(None, None, status=401),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "https://some.url:1234"},
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_user_form_unexpected_exception.opp):
    """Test we handle unexpected exception."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_server_status",
        side_effect=Exception(),
    ):
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "https://some.url:1234"},
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_user_form_duplicate.opp):
    """Test duplicate entries."""
    with _patch_glucose_readings(), _patch_server_status():
        unique_id = hash_from_url(CONFIG[CONF_URL])
        entry = MockConfigEntry(domain=DOMAIN, unique_id=unique_id)
        await.opp.config_entries.async_add(entry)
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONFIG,
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "already_configured"


def _patch_async_setup():
    return patch("openpeerpower.components.nightscout.async_setup", return_value=True)


def _patch_async_setup_entry():
    return patch(
        "openpeerpower.components.nightscout.async_setup_entry",
        return_value=True,
    )


def _patch_glucose_readings():
    return patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_sgvs",
        return_value=GLUCOSE_READINGS,
    )


def _patch_server_status():
    return patch(
        "openpeerpower.components.nightscout.NightscoutAPI.get_server_status",
        return_value=SERVER_STATUS,
    )
