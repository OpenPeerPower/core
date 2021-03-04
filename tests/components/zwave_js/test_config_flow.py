"""Test the Z-Wave JS config flow."""
import asyncio
from unittest.mock import DEFAULT, patch

import pytest
from zwave_js_server.version import VersionInfo

from openpeerpower import config_entries, setup
from openpeerpower.components.oppio.handler import OppioAPIError
from openpeerpower.components.zwave_js.config_flow import SERVER_VERSION_TIMEOUT, TITLE
from openpeerpower.components.zwave_js.const import DOMAIN

from tests.common import MockConfigEntry

ADDON_DISCOVERY_INFO = {
    "addon": "Z-Wave JS",
    "host": "host1",
    "port": 3001,
}


@pytest.fixture(name="supervisor")
def mock_supervisor_fixture():
    """Mock Supervisor."""
    with patch(
        "openpeerpower.components.zwave_js.config_flow.is_oppio", return_value=True
    ):
        yield


@pytest.fixture(name="discovery_info")
def discovery_info_fixture():
    """Return the discovery info from the supervisor."""
    return DEFAULT


@pytest.fixture(name="discovery_info_side_effect")
def discovery_info_side_effect_fixture():
    """Return the discovery info from the supervisor."""
    return None


@pytest.fixture(name="get_addon_discovery_info")
def mock_get_addon_discovery_info(discovery_info, discovery_info_side_effect):
    """Mock get add-on discovery info."""
    with patch(
        "openpeerpower.components.zwave_js.addon.async_get_addon_discovery_info",
        side_effect=discovery_info_side_effect,
        return_value=discovery_info,
    ) as get_addon_discovery_info:
        yield get_addon_discovery_info


@pytest.fixture(name="server_version_side_effect")
def server_version_side_effect_fixture():
    """Return the server version side effect."""
    return None


@pytest.fixture(name="get_server_version", autouse=True)
def mock_get_server_version(server_version_side_effect, server_version_timeout):
    """Mock server version."""
    version_info = VersionInfo(
        driver_version="mock-driver-version",
        server_version="mock-server-version",
        home_id=1234,
        min_schema_version=0,
        max_schema_version=1,
    )
    with patch(
        "openpeerpower.components.zwave_js.config_flow.get_server_version",
        side_effect=server_version_side_effect,
        return_value=version_info,
    ) as mock_version, patch(
        "openpeerpower.components.zwave_js.config_flow.SERVER_VERSION_TIMEOUT",
        new=server_version_timeout,
    ):
        yield mock_version


@pytest.fixture(name="server_version_timeout")
def mock_server_version_timeout():
    """Patch the timeout for getting server version."""
    return SERVER_VERSION_TIMEOUT


@pytest.fixture(name="addon_setup_time", autouse=True)
def mock_addon_setup_time():
    """Mock add-on setup sleep time."""
    with patch(
        "openpeerpower.components.zwave_js.config_flow.ADDON_SETUP_TIMEOUT", new=0
    ) as addon_setup_time:
        yield addon_setup_time


async def test_manual(opp):
    """Test we create an entry with manual step."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "ws://localhost:3000",
            },
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Z-Wave JS"
    assert result2["data"] == {
        "url": "ws://localhost:3000",
        "usb_path": None,
        "network_key": None,
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert result2["result"].unique_id == 1234


async def slow_server_version(*args):
    """Simulate a slow server version."""
    await asyncio.sleep(0.1)


@pytest.mark.parametrize(
    "url, server_version_side_effect, server_version_timeout, error",
    [
        (
            "not-ws-url",
            None,
            SERVER_VERSION_TIMEOUT,
            "invalid_ws_url",
        ),
        (
            "ws://localhost:3000",
            slow_server_version,
            0,
            "cannot_connect",
        ),
        (
            "ws://localhost:3000",
            Exception("Boom"),
            SERVER_VERSION_TIMEOUT,
            "unknown",
        ),
    ],
)
async def test_manual_errors(
    opp,
    url,
    error,
):
    """Test all errors with a manual set up."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": url,
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": error}


async def test_manual_already_configured(opp):
    """Test that only one unique instance is allowed."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, title=TITLE, unique_id=1234)
    entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://localhost:3000",
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_supervisor_discovery(
    opp, supervisor, addon_running, addon_options, get_addon_discovery_info
):
    """Test flow started from Supervisor discovery."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    addon_options["device"] = "/test"
    addon_options["network_key"] = "abc123"

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_OPPIO},
        data=ADDON_DISCOVERY_INFO,
    )

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "network_key": "abc123",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "discovery_info, server_version_side_effect",
    [({"config": ADDON_DISCOVERY_INFO}, asyncio.TimeoutError())],
)
async def test_supervisor_discovery_cannot_connect(
    opp, supervisor, get_addon_discovery_info
):
    """Test Supervisor discovery and cannot connect."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_OPPIO},
        data=ADDON_DISCOVERY_INFO,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_clean_discovery_on_user_create(
    opp, supervisor, addon_running, addon_options, get_addon_discovery_info
):
    """Test discovery flow is cleaned up when a user flow is finished."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    addon_options["device"] = "/test"
    addon_options["network_key"] = "abc123"

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_OPPIO},
        data=ADDON_DISCOVERY_INFO,
    )

    assert result["type"] == "form"

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": False}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "ws://localhost:3000",
            },
        )
        await opp.async_block_till_done()

    assert len(opp.config_entries.flow.async_progress()) == 0
    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://localhost:3000",
        "usb_path": None,
        "network_key": None,
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_abort_discovery_with_existing_entry(
    opp, supervisor, addon_running, addon_options
):
    """Test discovery flow is aborted if an entry already exists."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    entry = MockConfigEntry(
        domain=DOMAIN, data={"url": "ws://localhost:3000"}, title=TITLE, unique_id=1234
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_OPPIO},
        data=ADDON_DISCOVERY_INFO,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    # Assert that the entry data is updated with discovery info.
    assert entry.data["url"] == "ws://host1:3001"


async def test_discovery_addon_not_running(
    opp, supervisor, addon_installed, addon_options, set_addon_options, start_addon
):
    """Test discovery with add-on already installed but not running."""
    addon_options["device"] = None
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_OPPIO},
        data=ADDON_DISCOVERY_INFO,
    )

    assert result["step_id"] == "oppio_confirm"
    assert result["type"] == "form"

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await opp.async_block_till_done()
        result = await opp.config_entries.flow.async_configure(result["flow_id"])
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "network_key": "abc123",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_discovery_addon_not_installed(
    opp,
    supervisor,
    addon_installed,
    install_addon,
    addon_options,
    set_addon_options,
    start_addon,
):
    """Test discovery with add-on not installed."""
    addon_installed.return_value["version"] = None
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_OPPIO},
        data=ADDON_DISCOVERY_INFO,
    )

    assert result["step_id"] == "oppio_confirm"
    assert result["type"] == "form"

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["step_id"] == "install_addon"
    assert result["type"] == "progress"

    await opp.async_block_till_done()

    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await opp.async_block_till_done()
        result = await opp.config_entries.flow.async_configure(result["flow_id"])
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "network_key": "abc123",
        "use_addon": True,
        "integration_created_addon": True,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_not_addon(opp, supervisor):
    """Test opting out of add-on on Supervisor."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": False}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "ws://localhost:3000",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://localhost:3000",
        "usb_path": None,
        "network_key": None,
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_addon_already_configured(opp, supervisor):
    """Test add-on already configured leads to manual step."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"use_addon": True}, title=TITLE, unique_id=5678
    )
    entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "manual"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "ws://localhost:3000",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://localhost:3000",
        "usb_path": None,
        "network_key": None,
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_addon_running(
    opp,
    supervisor,
    addon_running,
    addon_options,
    get_addon_discovery_info,
):
    """Test add-on already running on Supervisor."""
    addon_options["device"] = "/test"
    addon_options["network_key"] = "abc123"
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], {"use_addon": True}
        )
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "network_key": "abc123",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "discovery_info, discovery_info_side_effect, server_version_side_effect, "
    "addon_info_side_effect, abort_reason",
    [
        (
            {"config": ADDON_DISCOVERY_INFO},
            OppioAPIError(),
            None,
            None,
            "addon_get_discovery_info_failed",
        ),
        (
            {"config": ADDON_DISCOVERY_INFO},
            None,
            asyncio.TimeoutError,
            None,
            "cannot_connect",
        ),
        (
            None,
            None,
            None,
            None,
            "addon_get_discovery_info_failed",
        ),
        (
            {"config": ADDON_DISCOVERY_INFO},
            None,
            None,
            OppioAPIError(),
            "addon_info_failed",
        ),
    ],
)
async def test_addon_running_failures(
    opp,
    supervisor,
    addon_running,
    addon_options,
    get_addon_discovery_info,
    abort_reason,
):
    """Test all failures when add-on is running."""
    addon_options["device"] = "/test"
    addon_options["network_key"] = "abc123"
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "abort"
    assert result["reason"] == abort_reason


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_addon_running_already_configured(
    opp, supervisor, addon_running, addon_options, get_addon_discovery_info
):
    """Test that only one unique instance is allowed when add-on is running."""
    addon_options["device"] = "/test"
    addon_options["network_key"] = "abc123"
    entry = MockConfigEntry(domain=DOMAIN, data={}, title=TITLE, unique_id=1234)
    entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_addon_installed(
    opp,
    supervisor,
    addon_installed,
    addon_options,
    set_addon_options,
    start_addon,
    get_addon_discovery_info,
):
    """Test add-on already installed but not running on Supervisor."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await opp.async_block_till_done()
        result = await opp.config_entries.flow.async_configure(result["flow_id"])
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "network_key": "abc123",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "discovery_info, start_addon_side_effect",
    [({"config": ADDON_DISCOVERY_INFO}, OppioAPIError())],
)
async def test_addon_installed_start_failure(
    opp,
    supervisor,
    addon_installed,
    addon_options,
    set_addon_options,
    start_addon,
    get_addon_discovery_info,
):
    """Test add-on start failure when add-on is installed."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    await opp.async_block_till_done()
    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == "abort"
    assert result["reason"] == "addon_start_failed"


@pytest.mark.parametrize(
    "discovery_info, server_version_side_effect",
    [
        (
            {"config": ADDON_DISCOVERY_INFO},
            asyncio.TimeoutError,
        ),
        (
            None,
            None,
        ),
    ],
)
async def test_addon_installed_failures(
    opp,
    supervisor,
    addon_installed,
    addon_options,
    set_addon_options,
    start_addon,
    get_addon_discovery_info,
):
    """Test all failures when add-on is installed."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    await opp.async_block_till_done()
    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == "abort"
    assert result["reason"] == "addon_start_failed"


@pytest.mark.parametrize(
    "set_addon_options_side_effect, discovery_info",
    [(OppioAPIError(), {"config": ADDON_DISCOVERY_INFO})],
)
async def test_addon_installed_set_options_failure(
    opp,
    supervisor,
    addon_installed,
    addon_options,
    set_addon_options,
    start_addon,
    get_addon_discovery_info,
):
    """Test all failures when add-on is installed."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "addon_set_config_failed"


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_addon_installed_already_configured(
    opp,
    supervisor,
    addon_installed,
    addon_options,
    set_addon_options,
    start_addon,
    get_addon_discovery_info,
):
    """Test that only one unique instance is allowed when add-on is installed."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, title=TITLE, unique_id=1234)
    entry.add_to_opp(opp)

    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    await opp.async_block_till_done()
    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize("discovery_info", [{"config": ADDON_DISCOVERY_INFO}])
async def test_addon_not_installed(
    opp,
    supervisor,
    addon_installed,
    install_addon,
    addon_options,
    set_addon_options,
    start_addon,
    get_addon_discovery_info,
):
    """Test add-on not installed."""
    addon_installed.return_value["version"] = None
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "install_addon"

    # Make sure the flow continues when the progress task is done.
    await opp.async_block_till_done()

    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == "form"
    assert result["step_id"] == "configure_addon"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"usb_path": "/test", "network_key": "abc123"}
    )

    assert result["type"] == "progress"
    assert result["step_id"] == "start_addon"

    with patch(
        "openpeerpower.components.zwave_js.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zwave_js.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await opp.async_block_till_done()
        result = await opp.config_entries.flow.async_configure(result["flow_id"])
        await opp.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "network_key": "abc123",
        "use_addon": True,
        "integration_created_addon": True,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_install_addon_failure(opp, supervisor, addon_installed, install_addon):
    """Test add-on install failure."""
    addon_installed.return_value["version"] = None
    install_addon.side_effect = OppioAPIError()
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "on_supervisor"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] == "progress"

    # Make sure the flow continues when the progress task is done.
    await opp.async_block_till_done()

    result = await opp.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == "abort"
    assert result["reason"] == "addon_install_failed"
