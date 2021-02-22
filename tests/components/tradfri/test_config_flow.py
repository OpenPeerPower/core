"""Test the Tradfri config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.tradfri import config_flow

from tests.common import MockConfigEntry


@pytest.fixture
def mock_auth():
    """Mock authenticate."""
    with patch(
        "openpeerpower.components.tradfri.config_flow.authenticate"
    ) as mock_auth:
        yield mock_auth


async def test_user_connection_successful.opp, mock_auth, mock_entry_setup):
    """Test a successful connection."""
    mock_auth.side_effect = lambda.opp, host, code: {"host": host, "gateway_id": "bla"}

    flow = await opp.config_entries.flow.async_init(
        "tradfri", context={"source": "user"}
    )

    result = await opp.config_entries.flow.async_configure(
        flow["flow_id"], {"host": "123.123.123.123", "security_code": "abcd"}
    )

    assert len(mock_entry_setup.mock_calls) == 1

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].data == {
        "host": "123.123.123.123",
        "gateway_id": "bla",
        "import_groups": False,
    }


async def test_user_connection_timeout.opp, mock_auth, mock_entry_setup):
    """Test a connection timeout."""
    mock_auth.side_effect = config_flow.AuthError("timeout")

    flow = await opp.config_entries.flow.async_init(
        "tradfri", context={"source": "user"}
    )

    result = await opp.config_entries.flow.async_configure(
        flow["flow_id"], {"host": "127.0.0.1", "security_code": "abcd"}
    )

    assert len(mock_entry_setup.mock_calls) == 0

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "timeout"}


async def test_user_connection_bad_key.opp, mock_auth, mock_entry_setup):
    """Test a connection with bad key."""
    mock_auth.side_effect = config_flow.AuthError("invalid_security_code")

    flow = await opp.config_entries.flow.async_init(
        "tradfri", context={"source": "user"}
    )

    result = await opp.config_entries.flow.async_configure(
        flow["flow_id"], {"host": "127.0.0.1", "security_code": "abcd"}
    )

    assert len(mock_entry_setup.mock_calls) == 0

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"security_code": "invalid_security_code"}


async def test_discovery_connection.opp, mock_auth, mock_entry_setup):
    """Test a connection via discovery."""
    mock_auth.side_effect = lambda.opp, host, code: {"host": host, "gateway_id": "bla"}

    flow = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "homekit"},
        data={"host": "123.123.123.123", "properties": {"id": "homekit-id"}},
    )

    result = await opp.config_entries.flow.async_configure(
        flow["flow_id"], {"security_code": "abcd"}
    )

    assert len(mock_entry_setup.mock_calls) == 1

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == "homekit-id"
    assert result["result"].data == {
        "host": "123.123.123.123",
        "gateway_id": "bla",
        "import_groups": False,
    }


async def test_import_connection.opp, mock_auth, mock_entry_setup):
    """Test a connection via import."""
    mock_auth.side_effect = lambda.opp, host, code: {
        "host": host,
        "gateway_id": "bla",
        "identity": "mock-iden",
        "key": "mock-key",
    }

    flow = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "import"},
        data={"host": "123.123.123.123", "import_groups": True},
    )

    result = await opp.config_entries.flow.async_configure(
        flow["flow_id"], {"security_code": "abcd"}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].data == {
        "host": "123.123.123.123",
        "gateway_id": "bla",
        "identity": "mock-iden",
        "key": "mock-key",
        "import_groups": True,
    }

    assert len(mock_entry_setup.mock_calls) == 1


async def test_import_connection_no_groups.opp, mock_auth, mock_entry_setup):
    """Test a connection via import and no groups allowed."""
    mock_auth.side_effect = lambda.opp, host, code: {
        "host": host,
        "gateway_id": "bla",
        "identity": "mock-iden",
        "key": "mock-key",
    }

    flow = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "import"},
        data={"host": "123.123.123.123", "import_groups": False},
    )

    result = await opp.config_entries.flow.async_configure(
        flow["flow_id"], {"security_code": "abcd"}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].data == {
        "host": "123.123.123.123",
        "gateway_id": "bla",
        "identity": "mock-iden",
        "key": "mock-key",
        "import_groups": False,
    }

    assert len(mock_entry_setup.mock_calls) == 1


async def test_import_connection_legacy.opp, mock_gateway_info, mock_entry_setup):
    """Test a connection via import."""
    mock_gateway_info.side_effect = lambda.opp, host, identity, key: {
        "host": host,
        "identity": identity,
        "key": key,
        "gateway_id": "mock-gateway",
    }

    result = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "import"},
        data={"host": "123.123.123.123", "key": "mock-key", "import_groups": True},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].data == {
        "host": "123.123.123.123",
        "gateway_id": "mock-gateway",
        "identity": "openpeerpower",
        "key": "mock-key",
        "import_groups": True,
    }

    assert len(mock_gateway_info.mock_calls) == 1
    assert len(mock_entry_setup.mock_calls) == 1


async def test_import_connection_legacy_no_groups(
    opp. mock_gateway_info, mock_entry_setup
):
    """Test a connection via legacy import and no groups allowed."""
    mock_gateway_info.side_effect = lambda.opp, host, identity, key: {
        "host": host,
        "identity": identity,
        "key": key,
        "gateway_id": "mock-gateway",
    }

    result = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "import"},
        data={"host": "123.123.123.123", "key": "mock-key", "import_groups": False},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].data == {
        "host": "123.123.123.123",
        "gateway_id": "mock-gateway",
        "identity": "openpeerpower",
        "key": "mock-key",
        "import_groups": False,
    }

    assert len(mock_gateway_info.mock_calls) == 1
    assert len(mock_entry_setup.mock_calls) == 1


async def test_discovery_duplicate_aborted.opp):
    """Test a duplicate discovery host aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain="tradfri", data={"host": "some-host"}, unique_id="homekit-id"
    )
    entry.add_to.opp.opp)

    flow = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "homekit"},
        data={"host": "new-host", "properties": {"id": "homekit-id"}},
    )

    assert flow["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert flow["reason"] == "already_configured"

    assert entry.data["host"] == "new-host"


async def test_import_duplicate_aborted.opp):
    """Test a duplicate import host is ignored."""
    MockConfigEntry(domain="tradfri", data={"host": "some-host"}).add_to.opp.opp)

    flow = await opp.config_entries.flow.async_init(
        "tradfri", context={"source": "import"}, data={"host": "some-host"}
    )

    assert flow["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert flow["reason"] == "already_configured"


async def test_duplicate_discovery.opp, mock_auth, mock_entry_setup):
    """Test a duplicate discovery in progress is ignored."""
    result = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "homekit"},
        data={"host": "123.123.123.123", "properties": {"id": "homekit-id"}},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    result2 = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "homekit"},
        data={"host": "123.123.123.123", "properties": {"id": "homekit-id"}},
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_discovery_updates_unique_id.opp):
    """Test a duplicate discovery host aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain="tradfri",
        data={"host": "some-host"},
    )
    entry.add_to.opp.opp)

    flow = await opp.config_entries.flow.async_init(
        "tradfri",
        context={"source": "homekit"},
        data={"host": "some-host", "properties": {"id": "homekit-id"}},
    )

    assert flow["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert flow["reason"] == "already_configured"

    assert entry.unique_id == "homekit-id"
