"""Test Axis component setup process."""
from unittest.mock import AsyncMock, Mock, patch

from openpeerpower.components import axis
from openpeerpower.components.axis.const import CONF_MODEL, DOMAIN as AXIS_DOMAIN
from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.const import (
    CONF_DEVICE,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from openpeerpowerr.helpers import entity_registry
from openpeerpowerr.helpers.device_registry import format_mac
from openpeerpowerr.setup import async_setup_component

from .test_device import MAC, setup_axis_integration

from tests.common import MockConfigEntry


async def test_setup_no_config.opp):
    """Test setup without configuration."""
    assert await async_setup_component.opp, AXIS_DOMAIN, {})
    assert AXIS_DOMAIN not in.opp.data


async def test_setup_entry.opp):
    """Test successful setup of entry."""
    await setup_axis_integration.opp)
    assert len.opp.data[AXIS_DOMAIN]) == 1
    assert format_mac(MAC) in.opp.data[AXIS_DOMAIN]


async def test_setup_entry_fails.opp):
    """Test successful setup of entry."""
    config_entry = MockConfigEntry(
        domain=AXIS_DOMAIN, data={CONF_MAC: "0123"}, version=3
    )
    config_entry.add_to_opp.opp)

    mock_device = Mock()
    mock_device.async_setup = AsyncMock(return_value=False)

    with patch.object(axis, "AxisNetworkDevice") as mock_device_class:
        mock_device_class.return_value = mock_device

        assert not await opp.config_entries.async_setup(config_entry.entry_id)

    assert not.opp.data[AXIS_DOMAIN]


async def test_unload_entry.opp):
    """Test successful unload of entry."""
    config_entry = await setup_axis_integration.opp)
    device = opp.data[AXIS_DOMAIN][config_entry.unique_id]
    assert.opp.data[AXIS_DOMAIN]

    assert await opp.config_entries.async_unload(device.config_entry.entry_id)
    assert not.opp.data[AXIS_DOMAIN]


async def test_migrate_entry.opp):
    """Test successful migration of entry data."""
    legacy_config = {
        CONF_DEVICE: {
            CONF_HOST: "1.2.3.4",
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
            CONF_PORT: 80,
        },
        CONF_MAC: "00408C123456",
        CONF_MODEL: "model",
        CONF_NAME: "name",
    }
    entry = MockConfigEntry(domain=AXIS_DOMAIN, data=legacy_config)

    assert entry.data == legacy_config
    assert entry.version == 1
    assert not entry.unique_id

    # Create entity entry to migrate to new unique ID
    registry = await entity_registry.async_get_registry.opp)
    registry.async_get_or_create(
        BINARY_SENSOR_DOMAIN,
        AXIS_DOMAIN,
        "00408C123456-vmd4-0",
        suggested_object_id="vmd4",
        config_entry=entry,
    )

    await entry.async_migrate.opp)

    assert entry.data == {
        CONF_DEVICE: {
            CONF_HOST: "1.2.3.4",
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
            CONF_PORT: 80,
        },
        CONF_HOST: "1.2.3.4",
        CONF_USERNAME: "username",
        CONF_PASSWORD: "password",
        CONF_PORT: 80,
        CONF_MAC: "00408C123456",
        CONF_MODEL: "model",
        CONF_NAME: "name",
    }
    assert entry.version == 2  # Keep version to support rollbacking
    assert entry.unique_id == "00:40:8c:12:34:56"

    vmd4_entity = registry.async_get("binary_sensor.vmd4")
    assert vmd4_entity.unique_id == "00:40:8c:12:34:56-vmd4-0"
