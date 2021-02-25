"""Test UniFi setup process."""
from unittest.mock import AsyncMock, Mock, patch

from openpeerpower.components import unifi
from openpeerpower.components.unifi import async_flatten_entry_data
from openpeerpower.components.unifi.const import CONF_CONTROLLER, DOMAIN as UNIFI_DOMAIN
from openpeerpower.setup import async_setup_component

from .test_controller import CONTROLLER_DATA, ENTRY_CONFIG, setup_unifi_integration

from tests.common import MockConfigEntry, mock_coro


async def test_setup_with_no_config(opp):
    """Test that we do not discover anything or try to set up a controller."""
    assert await async_setup_component(opp, UNIFI_DOMAIN, {}) is True
    assert UNIFI_DOMAIN not in.opp.data


async def test_successful_config_entry(opp, aioclient_mock):
    """Test that configured options for a host are loaded via config entry."""
    await setup_unifi_integration(opp, aioclient_mock)
    assert opp.data[UNIFI_DOMAIN]


async def test_controller_fail_setup_opp):
    """Test that a failed setup still stores controller."""
    with patch("openpeerpower.components.unifi.UniFiController") as mock_controller:
        mock_controller.return_value.async_setup = AsyncMock(return_value=False)
        await setup_unifi_integration.opp)

    assert opp.data[UNIFI_DOMAIN] == {}


async def test_controller_no_mac.opp):
    """Test that configured options for a host are loaded via config entry."""
    entry = MockConfigEntry(
        domain=UNIFI_DOMAIN,
        data=ENTRY_CONFIG,
        unique_id="1",
        version=1,
    )
    entry.add_to_opp(opp)
    mock_registry = Mock()
    with patch(
        "openpeerpower.components.unifi.UniFiController"
    ) as mock_controller, patch(
        "openpeerpower.helpers.device_registry.async_get_registry",
        return_value=mock_coro(mock_registry),
    ):
        mock_controller.return_value.async_setup = AsyncMock(return_value=True)
        mock_controller.return_value.mac = None
        assert await unifi.async_setup_entry(opp, entry) is True

    assert len(mock_controller.mock_calls) == 2

    assert len(mock_registry.mock_calls) == 0


async def test_flatten_entry_data.opp):
    """Verify entry data can be flattened."""
    entry = MockConfigEntry(
        domain=UNIFI_DOMAIN,
        data={CONF_CONTROLLER: CONTROLLER_DATA},
    )
    await async_flatten_entry_data(opp, entry)

    assert entry.data == ENTRY_CONFIG


async def test_unload_entry(opp, aioclient_mock):
    """Test being able to unload an entry."""
    config_entry = await setup_unifi_integration(opp, aioclient_mock)
    assert opp.data[UNIFI_DOMAIN]

    assert await unifi.async_unload_entry(opp, config_entry)
    assert not.opp.data[UNIFI_DOMAIN]
