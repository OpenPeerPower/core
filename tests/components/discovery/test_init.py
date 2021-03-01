"""The tests for the discovery component."""
from unittest.mock import MagicMock, patch

import pytest

from openpeerpower import config_entries
from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components import discovery
from openpeerpower.const import EVENT_OPENPEERPOWER_STARTED
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed, mock_coro

# One might consider to "mock" services, but it's easy enough to just use
# what is already available.
SERVICE = "yamaha"
SERVICE_COMPONENT = "media_player"

SERVICE_NO_PLATFORM = opp_ios"
SERVICE_NO_PLATFORM_COMPONENT = "ios"
SERVICE_INFO = {"key": "value"}  # Can be anything

UNKNOWN_SERVICE = "this_service_will_never_be_supported"

BASE_CONFIG = {discovery.DOMAIN: {"ignore": [], "enable": []}}

IGNORE_CONFIG = {discovery.DOMAIN: {"ignore": [SERVICE_NO_PLATFORM]}}


@pytest.fixture(autouse=True)
def netdisco_mock():
    """Mock netdisco."""
    with patch.dict("sys.modules", {"netdisco.discovery": MagicMock()}):
        yield


async def mock_discovery(opp, discoveries, config=BASE_CONFIG):
    """Mock discoveries."""
    with patch("openpeerpower.components.zeroconf.async_get_instance"), patch(
        "openpeerpower.components.zeroconf.async_setup", return_value=True
    ), patch.object(discovery, "_discover", discoveries), patch(
        "openpeerpower.components.discovery.async_discover", return_value=mock_coro()
    ) as mock_discover, patch(
        "openpeerpower.components.discovery.async_load_platform",
        return_value=mock_coro(),
    ) as mock_platform:
        assert await async_setup_component(opp, "discovery", config)
        await opp.async_block_till_done()
        await opp.async_start()
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await opp.async_block_till_done()
        async_fire_time_changed(opp, utcnow())
        # Work around an issue where our loop.call_soon not get caught
        await opp.async_block_till_done()
        await opp.async_block_till_done()

    return mock_discover, mock_platform


async def test_unknown_service(opp):
    """Test that unknown service is ignored."""

    def discover(netdisco, zeroconf_instance):
        """Fake discovery."""
        return [("this_service_will_never_be_supported", {"info": "some"})]

    mock_discover, mock_platform = await mock_discovery(opp, discover)

    assert not mock_discover.called
    assert not mock_platform.called


async def test_load_platform(opp):
    """Test load a platform."""

    def discover(netdisco, zeroconf_instance):
        """Fake discovery."""
        return [(SERVICE, SERVICE_INFO)]

    mock_discover, mock_platform = await mock_discovery(opp, discover)

    assert not mock_discover.called
    assert mock_platform.called
    mock_platform.assert_called_with(
        opp, SERVICE_COMPONENT, SERVICE, SERVICE_INFO, BASE_CONFIG
    )


async def test_load_component(opp):
    """Test load a component."""

    def discover(netdisco, zeroconf_instance):
        """Fake discovery."""
        return [(SERVICE_NO_PLATFORM, SERVICE_INFO)]

    mock_discover, mock_platform = await mock_discovery(opp, discover)

    assert mock_discover.called
    assert not mock_platform.called
    mock_discover.assert_called_with(
        opp,
        SERVICE_NO_PLATFORM,
        SERVICE_INFO,
        SERVICE_NO_PLATFORM_COMPONENT,
        BASE_CONFIG,
    )


async def test_ignore_service(opp):
    """Test ignore service."""

    def discover(netdisco, zeroconf_instance):
        """Fake discovery."""
        return [(SERVICE_NO_PLATFORM, SERVICE_INFO)]

    mock_discover, mock_platform = await mock_discovery(opp, discover, IGNORE_CONFIG)

    assert not mock_discover.called
    assert not mock_platform.called


async def test_discover_duplicates(opp):
    """Test load a component."""

    def discover(netdisco, zeroconf_instance):
        """Fake discovery."""
        return [
            (SERVICE_NO_PLATFORM, SERVICE_INFO),
            (SERVICE_NO_PLATFORM, SERVICE_INFO),
        ]

    mock_discover, mock_platform = await mock_discovery(opp, discover)

    assert mock_discover.called
    assert mock_discover.call_count == 1
    assert not mock_platform.called
    mock_discover.assert_called_with(
        opp,
        SERVICE_NO_PLATFORM,
        SERVICE_INFO,
        SERVICE_NO_PLATFORM_COMPONENT,
        BASE_CONFIG,
    )


async def test_discover_config_flow(opp):
    """Test discovery triggering a config flow."""
    discovery_info = {"hello": "world"}

    def discover(netdisco, zeroconf_instance):
        """Fake discovery."""
        return [("mock-service", discovery_info)]

    with patch.dict(
        discovery.CONFIG_ENTRY_HANDLERS, {"mock-service": "mock-component"}
    ), patch("openpeerpower.data_entry_flow.FlowManager.async_init") as m_init:
        await mock_discovery(opp, discover)

    assert len(m_init.mock_calls) == 1
    args, kwargs = m_init.mock_calls[0][1:]
    assert args == ("mock-component",)
    assert kwargs["context"]["source"] == config_entries.SOURCE_DISCOVERY
    assert kwargs["data"] == discovery_info
