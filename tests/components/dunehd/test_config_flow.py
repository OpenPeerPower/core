"""Define tests for the Dune HD config flow."""
from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.dunehd.const import DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import CONF_HOST

from tests.common import MockConfigEntry

CONFIG_HOSTNAME = {CONF_HOST: "dunehd-host"}
CONFIG_IP = {CONF_HOST: "10.10.10.12"}

DUNEHD_STATE = {"protocol_version": "4", "player_state": "navigator"}


async def test_import.opp):
    """Test that the import works."""
    with patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "dunehd-host"
        assert result["data"] == {CONF_HOST: "dunehd-host"}


async def test_import_cannot_connect.opp):
    """Test that errors are shown when cannot connect to the host during import."""
    with patch("pdunehd.DuneHDPlayer.update_state", return_value={}):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "cannot_connect"


async def test_import_duplicate_error(opp):
    """Test that errors are shown when duplicates are added during import."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "dunehd-host"},
        title="dunehd-host",
    )
    config_entry.add_to.opp.opp)

    with patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "already_configured"


async def test_user_invalid_host.opp):
    """Test that errors are shown when the host is invalid."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "invalid/host"}
    )

    assert result["errors"] == {CONF_HOST: "invalid_host"}


async def test_user_cannot_connect.opp):
    """Test that errors are shown when cannot connect to the host."""
    with patch("pdunehd.DuneHDPlayer.update_state", return_value={}):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_IP
        )

        assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_duplicate_error(opp):
    """Test that errors are shown when duplicates are added."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_HOSTNAME,
        title="dunehd-host",
    )
    config_entry.add_to.opp.opp)

    with patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_HOSTNAME
        )

        assert result["errors"] == {CONF_HOST: "already_configured"}


async def test_create_entry.opp):
    """Test that the user step works."""
    with patch("pdunehd.DuneHDPlayer.update_state", return_value=DUNEHD_STATE):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG_HOSTNAME
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "dunehd-host"
        assert result["data"] == {CONF_HOST: "dunehd-host"}
