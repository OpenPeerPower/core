"""Tests for the Config Entry Flow helper."""
from unittest.mock import Mock, patch

import pytest

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.config import async_process_op_core_config
from openpeerpower.helpers import config_entry_flow

from tests.common import MockConfigEntry, mock_entity_platform


@pytest.fixture
def discovery_flow_conf(opp):
    """Register a handler."""
    handler_conf = {"discovered": False}

    async def has_discovered_devices(opp):
        """Mock if we have discovered devices."""
        return handler_conf["discovered"]

    with patch.dict(config_entries.HANDLERS):
        config_entry_flow.register_discovery_flow(
            "test", "Test", has_discovered_devices
        )
        yield handler_conf


@pytest.fixture
def webhook_flow_conf(opp):
    """Register a handler."""
    with patch.dict(config_entries.HANDLERS):
        config_entry_flow.register_webhook_flow("test_single", "Test Single", {}, False)
        config_entry_flow.register_webhook_flow(
            "test_multiple", "Test Multiple", {}, True
        )
        yield {}


async def test_single_entry_allowed(opp, discovery_flow_conf):
    """Test only a single entry is allowed."""
    flow = config_entries.HANDLERS["test"]()
    flow.opp = opp
    flow.context = {}

    MockConfigEntry(domain="test").add_to_opp(opp)
    result = await flow.async_step_user()

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_user_no_devices_found(opp, discovery_flow_conf):
    """Test if no devices found."""
    flow = config_entries.HANDLERS["test"]()
    flow.opp = opp
    flow.context = {"source": config_entries.SOURCE_USER}
    result = await flow.async_step_confirm(user_input={})

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_has_confirmation(opp, discovery_flow_conf):
    """Test user requires confirmation to setup."""
    discovery_flow_conf["discovered"] = True
    mock_entity_platform(opp, "config_flow.test", None)

    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_USER}, data={}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    progress = opp.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0]["flow_id"] == result["flow_id"]
    assert progress[0]["context"] == {
        "confirm_only": True,
        "source": config_entries.SOURCE_USER,
        "unique_id": "test",
    }

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


@pytest.mark.parametrize(
    "source",
    [
        config_entries.SOURCE_DISCOVERY,
        config_entries.SOURCE_MQTT,
        config_entries.SOURCE_SSDP,
        config_entries.SOURCE_ZEROCONF,
        config_entries.SOURCE_DHCP,
    ],
)
async def test_discovery_single_instance(opp, discovery_flow_conf, source):
    """Test we not allow duplicates."""
    flow = config_entries.HANDLERS["test"]()
    flow.opp = opp
    flow.context = {}

    MockConfigEntry(domain="test").add_to_opp(opp)
    result = await getattr(flow, f"async_step_{source}")({})

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


@pytest.mark.parametrize(
    "source",
    [
        config_entries.SOURCE_DISCOVERY,
        config_entries.SOURCE_MQTT,
        config_entries.SOURCE_SSDP,
        config_entries.SOURCE_ZEROCONF,
        config_entries.SOURCE_DHCP,
    ],
)
async def test_discovery_confirmation(opp, discovery_flow_conf, source):
    """Test we ask for confirmation via discovery."""
    flow = config_entries.HANDLERS["test"]()
    flow.opp = opp
    flow.context = {"source": source}

    result = await getattr(flow, f"async_step_{source}")({})

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await flow.async_step_confirm({})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_multiple_discoveries(opp, discovery_flow_conf):
    """Test we only create one instance for multiple discoveries."""
    mock_entity_platform(opp, "config_flow.test", None)

    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    # Second discovery
    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_only_one_in_progress(opp, discovery_flow_conf):
    """Test a user initialized one will finish and cancel discovered one."""
    mock_entity_platform(opp, "config_flow.test", None)

    # Discovery starts flow
    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    # User starts flow
    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_USER}, data={}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    # Discovery flow has not been aborted
    assert len(opp.config_entries.flow.async_progress()) == 2

    # Discovery should be aborted once user confirms
    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert len(opp.config_entries.flow.async_progress()) == 0


async def test_import_abort_discovery(opp, discovery_flow_conf):
    """Test import will finish and cancel discovered one."""
    mock_entity_platform(opp, "config_flow.test", None)

    # Discovery starts flow
    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    # Start import flow
    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_IMPORT}, data={}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

    # Discovery flow has been aborted
    assert len(opp.config_entries.flow.async_progress()) == 0


async def test_import_no_confirmation(opp, discovery_flow_conf):
    """Test import requires no confirmation to set up."""
    flow = config_entries.HANDLERS["test"]()
    flow.opp = opp
    flow.context = {}
    discovery_flow_conf["discovered"] = True

    result = await flow.async_step_import(None)
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY


async def test_import_single_instance(opp, discovery_flow_conf):
    """Test import doesn't create second instance."""
    flow = config_entries.HANDLERS["test"]()
    flow.opp = opp
    flow.context = {}
    discovery_flow_conf["discovered"] = True
    MockConfigEntry(domain="test").add_to_opp(opp)

    result = await flow.async_step_import(None)
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_ignored_discoveries(opp, discovery_flow_conf):
    """Test we can ignore discovered entries."""
    mock_entity_platform(opp, "config_flow.test", None)

    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

    flow = next(
        (
            flw
            for flw in opp.config_entries.flow.async_progress()
            if flw["flow_id"] == result["flow_id"]
        ),
        None,
    )

    # Ignore it.
    await opp.config_entries.flow.async_init(
        flow["handler"],
        context={"source": config_entries.SOURCE_IGNORE},
        data={"unique_id": flow["context"]["unique_id"], "title": "Ignored Entry"},
    )

    # Second discovery should be aborted
    result = await opp.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_webhook_single_entry_allowed(opp, webhook_flow_conf):
    """Test only a single entry is allowed."""
    flow = config_entries.HANDLERS["test_single"]()
    flow.opp = opp

    MockConfigEntry(domain="test_single").add_to_opp(opp)
    result = await flow.async_step_user()

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_webhook_multiple_entries_allowed(opp, webhook_flow_conf):
    """Test multiple entries are allowed when specified."""
    flow = config_entries.HANDLERS["test_multiple"]()
    flow.opp = opp

    MockConfigEntry(domain="test_multiple").add_to_opp(opp)
    opp.config.api = Mock(base_url="http://example.com")

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_webhook_config_flow_registers_webhook(opp, webhook_flow_conf):
    """Test setting up an entry creates a webhook."""
    flow = config_entries.HANDLERS["test_single"]()
    flow.opp = opp

    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com"},
    )
    result = await flow.async_step_user(user_input={})

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"]["webhook_id"] is not None


async def test_warning_deprecated_connection_class(opp, caplog):
    """Test that we log a warning when the connection_class is used."""
    discovery_function = Mock()
    with patch.dict(config_entries.HANDLERS):
        config_entry_flow.register_discovery_flow(
            "test", "Test", discovery_function, connection_class="local_polling"
        )

    assert "integration is setting a connection_class" in caplog.text
