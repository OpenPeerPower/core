"""Test the Volumio config flow."""
from unittest.mock import patch

from openpeerpower import config_entries
from openpeerpower.components.volumio.config_flow import CannotConnectError
from openpeerpower.components.volumio.const import DOMAIN

from tests.common import MockConfigEntry

TEST_SYSTEM_INFO = {"id": "1111-1111-1111-1111", "name": "TestVolumio"}


TEST_CONNECTION = {
    "host": "1.1.1.1",
    "port": 3000,
}


TEST_DISCOVERY = {
    "host": "1.1.1.1",
    "port": 3000,
    "properties": {"volumioName": "discovered", "UUID": "2222-2222-2222-2222"},
}

TEST_DISCOVERY_RESULT = {
    "host": TEST_DISCOVERY["host"],
    "port": TEST_DISCOVERY["port"],
    "id": TEST_DISCOVERY["properties"]["UUID"],
    "name": TEST_DISCOVERY["properties"]["volumioName"],
}


async def test_form(opp):
    """Test we get the form."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        return_value=TEST_SYSTEM_INFO,
    ), patch(
        "openpeerpower.components.volumio.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.volumio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "TestVolumio"
    assert result2["data"] == {**TEST_SYSTEM_INFO, **TEST_CONNECTION}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_updates_unique_id(opp):
    """Test a duplicate id aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_SYSTEM_INFO["id"],
        data={
            "host": "dummy",
            "port": 11,
            "name": "dummy",
            "id": TEST_SYSTEM_INFO["id"],
        },
    )

    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        return_value=TEST_SYSTEM_INFO,
    ), patch("openpeerpower.components.volumio.async_setup", return_value=True), patch(
        "openpeerpower.components.volumio.async_setup_entry",
        return_value=True,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"

    assert entry.data == {**TEST_SYSTEM_INFO, **TEST_CONNECTION}


async def test_empty_system_info(opp):
    """Test old volumio versions with empty system info."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        return_value={},
    ), patch(
        "openpeerpower.components.volumio.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.volumio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == TEST_CONNECTION["host"]
    assert result2["data"] == {
        "host": TEST_CONNECTION["host"],
        "port": TEST_CONNECTION["port"],
        "name": TEST_CONNECTION["host"],
        "id": None,
    }

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        side_effect=CannotConnectError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_exception(opp):
    """Test we handle generic error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_discovery(opp):
    """Test discovery flow works."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "zeroconf"}, data=TEST_DISCOVERY
    )

    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        return_value=TEST_SYSTEM_INFO,
    ), patch(
        "openpeerpower.components.volumio.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.volumio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == TEST_DISCOVERY_RESULT["name"]
    assert result2["data"] == TEST_DISCOVERY_RESULT

    assert result2["result"]
    assert result2["result"].unique_id == TEST_DISCOVERY_RESULT["id"]

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_discovery_cannot_connect(opp):
    """Test discovery aborts if cannot connect."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "zeroconf"}, data=TEST_DISCOVERY
    )

    with patch(
        "openpeerpower.components.volumio.config_flow.Volumio.get_system_info",
        side_effect=CannotConnectError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "cannot_connect"


async def test_discovery_duplicate_data(opp):
    """Test discovery aborts if same mDNS packet arrives."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "zeroconf"}, data=TEST_DISCOVERY
    )
    assert result["type"] == "form"
    assert result["step_id"] == "discovery_confirm"

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "zeroconf"}, data=TEST_DISCOVERY
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_in_progress"


async def test_discovery_updates_unique_id(opp):
    """Test a duplicate discovery id aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_DISCOVERY_RESULT["id"],
        data={
            "host": "dummy",
            "port": 11,
            "name": "dummy",
            "id": TEST_DISCOVERY_RESULT["id"],
        },
        state=config_entries.ENTRY_STATE_SETUP_RETRY,
    )

    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.volumio.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.volumio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "zeroconf"}, data=TEST_DISCOVERY
        )
        await opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert entry.data == TEST_DISCOVERY_RESULT
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
