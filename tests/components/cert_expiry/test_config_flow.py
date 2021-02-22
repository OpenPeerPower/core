"""Tests for the Cert Expiry config flow."""
import socket
import ssl
from unittest.mock import patch

from openpeerpower import data_entry_flow
from openpeerpower.components.cert_expiry.const import DEFAULT_PORT, DOMAIN
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT

from .const import HOST, PORT
from .helpers import future_timestamp

from tests.common import MockConfigEntry


async def test_user.opp):
    """Test user config."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.cert_expiry.config_flow.get_cert_expiry_timestamp"
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST, CONF_PORT: PORT}
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT
    assert result["result"].unique_id == f"{HOST}:{PORT}"

    with patch("openpeerpower.components.cert_expiry.sensor.async_setup_entry"):
        await.opp.async_block_till_done()


async def test_user_with_bad_cert.opp):
    """Test user config with bad certificate."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=ssl.SSLError("some error"),
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST, CONF_PORT: PORT}
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT
    assert result["result"].unique_id == f"{HOST}:{PORT}"

    with patch("openpeerpower.components.cert_expiry.sensor.async_setup_entry"):
        await.opp.async_block_till_done()


async def test_import_host_only.opp):
    """Test import with host only."""
    with patch(
        "openpeerpower.components.cert_expiry.config_flow.get_cert_expiry_timestamp"
    ), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data={CONF_HOST: HOST}
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == DEFAULT_PORT
    assert result["result"].unique_id == f"{HOST}:{DEFAULT_PORT}"


async def test_import_host_and_port.opp):
    """Test import with host and port."""
    with patch(
        "openpeerpower.components.cert_expiry.config_flow.get_cert_expiry_timestamp"
    ), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data={CONF_HOST: HOST, CONF_PORT: PORT},
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT
    assert result["result"].unique_id == f"{HOST}:{PORT}"


async def test_import_non_default_port.opp):
    """Test import with host and non-default port."""
    with patch(
        "openpeerpower.components.cert_expiry.config_flow.get_cert_expiry_timestamp"
    ), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data={CONF_HOST: HOST, CONF_PORT: 888}
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"{HOST}:888"
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == 888
    assert result["result"].unique_id == f"{HOST}:888"


async def test_import_with_name.opp):
    """Test import with name (deprecated)."""
    with patch(
        "openpeerpower.components.cert_expiry.config_flow.get_cert_expiry_timestamp"
    ), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data={CONF_NAME: "legacy", CONF_HOST: HOST, CONF_PORT: PORT},
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_PORT] == PORT
    assert result["result"].unique_id == f"{HOST}:{PORT}"


async def test_bad_import.opp):
    """Test import step."""
    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=ConnectionRefusedError(),
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "import"}, data={CONF_HOST: HOST}
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "import_failed"


async def test_abort_if_already_setup_opp):
    """Test we abort if the cert is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    ).add_to.opp.opp)

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "import"}, data={CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data={CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_abort_on_socket_failed.opp):
    """Test we abort of we have errors during socket creation."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=socket.gaierror(),
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "resolve_failed"}

    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=socket.timeout(),
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "connection_timeout"}

    with patch(
        "openpeerpower.components.cert_expiry.helper.get_cert",
        side_effect=ConnectionRefusedError,
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: HOST}
        )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {CONF_HOST: "connection_refused"}
