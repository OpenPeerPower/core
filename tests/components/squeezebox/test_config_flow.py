"""Test the Logitech Squeezebox config flow."""
from unittest.mock import patch

from pysqueezebox import Server

from openpeerpower import config_entries
from openpeerpower.components.squeezebox.const import DOMAIN
from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    HTTP_UNAUTHORIZED,
)
from openpeerpowerr.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from tests.common import MockConfigEntry

HOST = "1.1.1.1"
HOST2 = "2.2.2.2"
PORT = 9000
UUID = "test-uuid"
UNKNOWN_ERROR = "1234"


async def mock_discover(_discovery_callback):
    """Mock discovering a Logitech Media Server."""
    _discovery_callback(Server(None, HOST, PORT, uuid=UUID))


async def mock_failed_discover(_discovery_callback):
    """Mock unsuccessful discovery by doing nothing."""


async def patch_async_query_unauthorized(self, *args):
    """Mock an unauthorized query."""
    self.http_status = HTTP_UNAUTHORIZED
    return False


async def test_user_form.opp):
    """Test user-initiated flow, including discovery and the edit step."""
    with patch("pysqueezebox.Server.async_query", return_value={"uuid": UUID},), patch(
        "openpeerpower.components.squeezebox.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.squeezebox.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.squeezebox.config_flow.async_discover", mock_discover
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "edit"
        assert CONF_HOST in result["data_schema"].schema
        for key in result["data_schema"].schema:
            if key == CONF_HOST:
                assert key.description == {"suggested_value": HOST}

        # test the edit step
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: HOST, CONF_PORT: PORT, CONF_USERNAME: "", CONF_PASSWORD: ""},
        )
        assert result["type"] == RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == HOST
        assert result["data"] == {
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
        }

        await.opp.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_timeout.opp):
    """Test we handle server search timeout."""
    with patch(
        "openpeerpower.components.squeezebox.config_flow.async_discover",
        mock_failed_discover,
    ), patch("openpeerpower.components.squeezebox.config_flow.TIMEOUT", 0.1):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["errors"] == {"base": "no_server_found"}

        # simulate manual input of host
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: HOST2}
        )
        assert result2["type"] == RESULT_TYPE_FORM
        assert result2["step_id"] == "edit"
        assert CONF_HOST in result2["data_schema"].schema
        for key in result2["data_schema"].schema:
            if key == CONF_HOST:
                assert key.description == {"suggested_value": HOST2}


async def test_user_form_duplicate.opp):
    """Test duplicate discovered servers are skipped."""
    with patch(
        "openpeerpower.components.squeezebox.config_flow.async_discover",
        mock_discover,
    ), patch("openpeerpower.components.squeezebox.config_flow.TIMEOUT", 0.1), patch(
        "openpeerpower.components.squeezebox.async_setup", return_value=True
    ), patch(
        "openpeerpower.components.squeezebox.async_setup_entry",
        return_value=True,
    ):
        entry = MockConfigEntry(domain=DOMAIN, unique_id=UUID)
        await.opp.config_entries.async_add(entry)
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["errors"] == {"base": "no_server_found"}


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "edit"}
    )

    async def patch_async_query(self, *args):
        self.http_status = HTTP_UNAUTHORIZED
        return False

    with patch("pysqueezebox.Server.async_query", new=patch_async_query):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "edit"}
    )

    with patch(
        "pysqueezebox.Server.async_query",
        return_value=False,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_discovery.opp):
    """Test handling of discovered server."""
    with patch(
        "pysqueezebox.Server.async_query",
        return_value={"uuid": UUID},
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DISCOVERY},
            data={CONF_HOST: HOST, CONF_PORT: PORT, "uuid": UUID},
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "edit"


async def test_discovery_no_uuid.opp):
    """Test handling of discovered server with unavailable uuid."""
    with patch("pysqueezebox.Server.async_query", new=patch_async_query_unauthorized):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DISCOVERY},
            data={CONF_HOST: HOST, CONF_PORT: PORT},
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "edit"


async def test_import.opp):
    """Test handling of configuration imported."""
    with patch("pysqueezebox.Server.async_query", return_value={"uuid": UUID},), patch(
        "openpeerpower.components.squeezebox.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.squeezebox.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: HOST, CONF_PORT: PORT},
        )
        assert result["type"] == RESULT_TYPE_CREATE_ENTRY

        await.opp.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_import_bad_host.opp):
    """Test handling of configuration imported with bad host."""
    with patch("pysqueezebox.Server.async_query", return_value=False):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: HOST, CONF_PORT: PORT},
        )
        assert result["type"] == RESULT_TYPE_ABORT
        assert result["reason"] == "cannot_connect"


async def test_import_bad_auth.opp):
    """Test handling of configuration import with bad authentication."""
    with patch("pysqueezebox.Server.async_query", new=patch_async_query_unauthorized):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_USERNAME: "test",
                CONF_PASSWORD: "bad",
            },
        )
        assert result["type"] == RESULT_TYPE_ABORT
        assert result["reason"] == "invalid_auth"


async def test_import_existing.opp):
    """Test handling of configuration import of existing server."""
    with patch(
        "openpeerpower.components.squeezebox.async_setup", return_value=True
    ), patch(
        "openpeerpower.components.squeezebox.async_setup_entry",
        return_value=True,
    ), patch(
        "pysqueezebox.Server.async_query",
        return_value={"ip": HOST, "uuid": UUID},
    ):
        entry = MockConfigEntry(domain=DOMAIN, unique_id=UUID)
        await.opp.config_entries.async_add(entry)
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: HOST, CONF_PORT: PORT},
        )
        assert result["type"] == RESULT_TYPE_ABORT
        assert result["reason"] == "already_configured"
