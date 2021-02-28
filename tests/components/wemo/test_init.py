"""Tests for the wemo component."""
from datetime import timedelta
from unittest.mock import create_autospec, patch

import pywemo

from openpeerpower.components.wemo import CONF_DISCOVERY, CONF_STATIC, WemoDiscovery
from openpeerpower.components.wemo.const import DOMAIN
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt

from .conftest import MOCK_HOST, MOCK_NAME, MOCK_PORT, MOCK_SERIAL_NUMBER

from tests.common import async_fire_time_changed


async def test_config_no_config(opp):
    """Component setup succeeds when there are no config entry for the domain."""
    assert await async_setup_component(opp, DOMAIN, {})


async def test_config_no_static(opp):
    """Component setup succeeds when there are no static config entries."""
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_DISCOVERY: False}})


async def test_static_duplicate_static_entry(opp, pywemo_device):
    """Duplicate static entries are merged into a single entity."""
    static_config_entry = f"{MOCK_HOST}:{MOCK_PORT}"
    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_DISCOVERY: False,
                CONF_STATIC: [
                    static_config_entry,
                    static_config_entry,
                ],
            },
        },
    )
    await opp.async_block_till_done()
    entity_reg = await opp.helpers.entity_registry.async_get_registry()
    entity_entries = list(entity_reg.entities.values())
    assert len(entity_entries) == 1


async def test_static_config_with_port(opp, pywemo_device):
    """Static device with host and port is added and removed."""
    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_DISCOVERY: False,
                CONF_STATIC: [f"{MOCK_HOST}:{MOCK_PORT}"],
            },
        },
    )
    await opp.async_block_till_done()
    entity_reg = await opp.helpers.entity_registry.async_get_registry()
    entity_entries = list(entity_reg.entities.values())
    assert len(entity_entries) == 1


async def test_static_config_without_port(opp, pywemo_device):
    """Static device with host and no port is added and removed."""
    assert await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_DISCOVERY: False,
                CONF_STATIC: [MOCK_HOST],
            },
        },
    )
    await opp.async_block_till_done()
    entity_reg = await opp.helpers.entity_registry.async_get_registry()
    entity_entries = list(entity_reg.entities.values())
    assert len(entity_entries) == 1


async def test_static_config_with_invalid_host(opp):
    """Component setup fails if a static host is invalid."""
    setup_success = await async_setup_component(
        opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_DISCOVERY: False,
                CONF_STATIC: [""],
            },
        },
    )
    assert not setup_success


async def test_discovery(opp, pywemo_registry):
    """Verify that discovery dispatches devices to the platform for setup."""

    def create_device(uuid, location):
        """Create a unique mock Motion detector device for each counter value."""
        device = create_autospec(pywemo.Motion, instance=True)
        device.host = location
        device.port = MOCK_PORT
        device.name = f"{MOCK_NAME}_{uuid}"
        device.serialnumber = f"{MOCK_SERIAL_NUMBER}_{uuid}"
        device.model_name = "Motion"
        device.get_state.return_value = 0  # Default to Off
        return device

    def create_upnp_entry(counter):
        return pywemo.ssdp.UPNPEntry.from_response(
            "\r\n".join(
                [
                    "",
                    f"LOCATION: http://192.168.1.100:{counter}/setup.xml",
                    f"USN: uuid:Socket-1_0-SERIAL{counter}::upnp:rootdevice",
                    "",
                ]
            )
        )

    upnp_entries = [create_upnp_entry(0), create_upnp_entry(1)]
    # Setup the component and start discovery.
    with patch(
        "pywemo.discovery.device_from_uuid_and_location", side_effect=create_device
    ), patch("pywemo.ssdp.scan", return_value=upnp_entries) as mock_scan:
        assert await async_setup_component(
            opp. DOMAIN, {DOMAIN: {CONF_DISCOVERY: True}}
        )
        await pywemo_registry.semaphore.acquire()  # Returns after platform setup.
        mock_scan.assert_called()
        # Add two of the same entries to test deduplication.
        upnp_entries.extend([create_upnp_entry(2), create_upnp_entry(2)])

        # Test that discovery runs periodically and the async_dispatcher_send code works.
        async_fire_time_changed(
            opp,
            dt.utcnow()
            + timedelta(seconds=WemoDiscovery.ADDITIONAL_SECONDS_BETWEEN_SCANS + 1),
        )
        await opp.async_block_till_done()

    # Verify that the expected number of devices were setup.
    entity_reg = await opp.helpers.entity_registry.async_get_registry()
    entity_entries = list(entity_reg.entities.values())
    assert len(entity_entries) == 3

    # Verify that.opp stops cleanly.
    await opp.async_stop()
    await opp.async_block_till_done()
