"""The sensor tests for the Ruckus Unleashed platform."""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.components.ruckus_unleashed import API_MAC, DOMAIN
from openpeerpower.components.ruckus_unleashed.const import API_AP, API_ID, API_NAME
from openpeerpower.const import STATE_HOME, STATE_NOT_HOME, STATE_UNAVAILABLE
from openpeerpower.helpers import entity_registry
from openpeerpower.helpers.device_registry import CONNECTION_NETWORK_MAC
from openpeerpower.util import utcnow

from tests.common import async_fire_time_changed
from tests.components.ruckus_unleashed import (
    DEFAULT_AP_INFO,
    DEFAULT_SYSTEM_INFO,
    DEFAULT_TITLE,
    DEFAULT_UNIQUE_ID,
    TEST_CLIENT,
    TEST_CLIENT_ENTITY_ID,
    init_integration,
    mock_config_entry,
)


async def test_client_connected(opp):
    """Test client connected."""
    await init_integration(opp)

    future = utcnow() + timedelta(minutes=60)
    with patch(
        "openpeerpower.components.ruckus_unleashed.RuckusUnleashedDataUpdateCoordinator._fetch_clients",
        return_value={
            TEST_CLIENT[API_MAC]: TEST_CLIENT,
        },
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()
        await opp.helpers.entity_component.async_update_entity(TEST_CLIENT_ENTITY_ID)

    test_client = opp.states.get(TEST_CLIENT_ENTITY_ID)
    assert test_client.state == STATE_HOME


async def test_client_disconnected(opp):
    """Test client disconnected."""
    await init_integration(opp)

    future = utcnow() + timedelta(minutes=60)
    with patch(
        "openpeerpower.components.ruckus_unleashed.RuckusUnleashedDataUpdateCoordinator._fetch_clients",
        return_value={},
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        await opp.helpers.entity_component.async_update_entity(TEST_CLIENT_ENTITY_ID)
        test_client = opp.states.get(TEST_CLIENT_ENTITY_ID)
        assert test_client.state == STATE_NOT_HOME


async def test_clients_update_failed(opp):
    """Test failed update."""
    await init_integration(opp)

    future = utcnow() + timedelta(minutes=60)
    with patch(
        "openpeerpower.components.ruckus_unleashed.RuckusUnleashedDataUpdateCoordinator._fetch_clients",
        side_effect=ConnectionError,
    ):
        async_fire_time_changed(opp, future)
        await opp.async_block_till_done()

        await opp.helpers.entity_component.async_update_entity(TEST_CLIENT_ENTITY_ID)
        test_client = opp.states.get(TEST_CLIENT_ENTITY_ID)
        assert test_client.state == STATE_UNAVAILABLE


async def test_restoring_clients(opp):
    """Test restoring existing device_tracker entities if not detected on startup."""
    entry = mock_config_entry()
    entry.add_to_opp(opp)

    registry = await entity_registry.async_get_registry(opp)
    registry.async_get_or_create(
        "device_tracker",
        DOMAIN,
        DEFAULT_UNIQUE_ID,
        suggested_object_id="ruckus_test_device",
        config_entry=entry,
    )

    with patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.connect",
        return_value=None,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.mesh_name",
        return_value=DEFAULT_TITLE,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.system_info",
        return_value=DEFAULT_SYSTEM_INFO,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.Ruckus.ap_info",
        return_value=DEFAULT_AP_INFO,
    ), patch(
        "openpeerpower.components.ruckus_unleashed.RuckusUnleashedDataUpdateCoordinator._fetch_clients",
        return_value={},
    ):
        entry.add_to_opp(opp)
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    device = opp.states.get(TEST_CLIENT_ENTITY_ID)
    assert device is not None
    assert device.state == STATE_NOT_HOME


async def test_client_device_setup_opp):
    """Test a client device is created."""
    await init_integration(opp)

    router_info = DEFAULT_AP_INFO[API_AP][API_ID]["1"]

    device_registry = await opp.helpers.device_registry.async_get_registry()
    client_device = device_registry.async_get_device(
        identifiers={},
        connections={(CONNECTION_NETWORK_MAC, TEST_CLIENT[API_MAC])},
    )
    router_device = device_registry.async_get_device(
        identifiers={(CONNECTION_NETWORK_MAC, router_info[API_MAC])},
        connections={(CONNECTION_NETWORK_MAC, router_info[API_MAC])},
    )

    assert client_device
    assert client_device.name == TEST_CLIENT[API_NAME]
    assert client_device.via_device_id == router_device.id
