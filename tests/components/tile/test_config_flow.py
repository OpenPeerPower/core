"""Define tests for the Tile config flow."""
from unittest.mock import patch

from pytile.errors import TileError

from openpeerpower import data_entry_flow
from openpeerpower.components.tile import DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    conf = {
        CONF_USERNAME: "user@host.com",
        CONF_PASSWORD: "123abc",
    }

    MockConfigEntry(domain=DOMAIN, unique_id="user@host.com", data=conf).add_to_opp(
        opp
    )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=conf
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_credentials(opp):
    """Test that invalid credentials key throws an error."""
    conf = {
        CONF_USERNAME: "user@host.com",
        CONF_PASSWORD: "123abc",
    }

    with patch(
        "openpeerpower.components.tile.config_flow.async_login",
        side_effect=TileError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_step_import(opp):
    """Test that the import step works."""
    conf = {
        CONF_USERNAME: "user@host.com",
        CONF_PASSWORD: "123abc",
    }

    with patch(
        "openpeerpower.components.tile.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.tile.config_flow.async_login"):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@host.com"
        assert result["data"] == {
            CONF_USERNAME: "user@host.com",
            CONF_PASSWORD: "123abc",
        }


async def test_step_user(opp):
    """Test that the user step works."""
    conf = {
        CONF_USERNAME: "user@host.com",
        CONF_PASSWORD: "123abc",
    }

    with patch(
        "openpeerpower.components.tile.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.tile.config_flow.async_login"):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=conf
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "user@host.com"
        assert result["data"] == {
            CONF_USERNAME: "user@host.com",
            CONF_PASSWORD: "123abc",
        }
