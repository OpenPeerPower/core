"""Test UniFi setup process."""
from unittest.mock import AsyncMock, patch

from openpeerpower.components import unifi
from openpeerpower.components.unifi import async_flatten_entry_data
from openpeerpower.components.unifi.const import CONF_CONTROLLER, DOMAIN as UNIFI_DOMAIN
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC
from openpeerpower.setup import async_setup_component

from .test_controller import (
    CONTROLLER_DATA,
    DEFAULT_CONFIG_ENTRY_ID,
    ENTRY_CONFIG,
    setup_unifi_integration,
)

from tests.common import MockConfigEntry


async def test_setup_with_no_config(opp):
    """Test that we do not discover anything or try to set up a controller."""
    assert await async_setup_component(opp, UNIFI_DOMAIN, {}) is True
    assert UNIFI_DOMAIN not in opp.data


async def test_successful_config_entry(opp, aioclient_mock):
    """Test that configured options for a host are loaded via config entry."""
    await setup_unifi_integration(opp, aioclient_mock, unique_id=None)
    assert opp.data[UNIFI_DOMAIN]


async def test_controller_fail_setup(opp):
    """Test that a failed setup still stores controller."""
    with patch("openpeerpower.components.unifi.UniFiController") as mock_controller:
        mock_controller.return_value.async_setup = AsyncMock(return_value=False)
        await setup_unifi_integration(opp)

    assert opp.data[UNIFI_DOMAIN] == {}


async def test_controller_mac(opp):
    """Test that configured options for a host are loaded via config entry."""
    entry = MockConfigEntry(
        domain=UNIFI_DOMAIN, data=ENTRY_CONFIG, unique_id="1", entry_id=1
    )
    entry.add_to_opp(opp)

    with patch("openpeerpower.components.unifi.UniFiController") as mock_controller:
        mock_controller.return_value.async_setup = AsyncMock(return_value=True)
        mock_controller.return_value.mac = "mac1"
        assert await unifi.async_setup_entry(opp, entry) is True

    assert len(mock_controller.mock_calls) == 2

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, connections={(CONNECTION_NETWORK_MAC, "mac1")}
    )
    assert device.manufacturer == "Ubiquiti Networks"
    assert device.model == "UniFi Controller"
    assert device.name == "UniFi Controller"
    assert device.sw_version is None


async def test_flatten_entry_data(opp):
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

    assert await opp.config_entries.async_unload(config_entry.entry_id)
    assert not opp.data[UNIFI_DOMAIN]


async def test_wireless_clients(opp, opp_storage, aioclient_mock):
    """Verify wireless clients class."""
    opp_storage[unifi.STORAGE_KEY] = {
        "version": unifi.STORAGE_VERSION,
        "data": {
            DEFAULT_CONFIG_ENTRY_ID: {
                "wireless_devices": ["00:00:00:00:00:00", "00:00:00:00:00:01"]
            }
        },
    }

    client_1 = {
        "hostname": "client_1",
        "ip": "10.0.0.1",
        "is_wired": False,
        "mac": "00:00:00:00:00:01",
    }
    client_2 = {
        "hostname": "client_2",
        "ip": "10.0.0.2",
        "is_wired": False,
        "mac": "00:00:00:00:00:02",
    }
    config_entry = await setup_unifi_integration(
        opp, aioclient_mock, clients_response=[client_1, client_2]
    )

    for mac in [
        "00:00:00:00:00:00",
        "00:00:00:00:00:01",
        "00:00:00:00:00:02",
    ]:
        assert (
            mac
            in opp_storage[unifi.STORAGE_KEY]["data"][config_entry.entry_id][
                "wireless_devices"
            ]
        )
