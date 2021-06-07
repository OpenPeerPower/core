"""Tests for 1-Wire config flow."""
from unittest.mock import patch

from pyownet.protocol import ConnError, OwnetError

from openpeerpower.components.onewire.const import CONF_TYPE_OWSERVER, DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config_entries import SOURCE_USER, ConfigEntryState
from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_TYPE
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.setup import async_setup_component

from . import (
    setup_onewire_owserver_integration,
    setup_onewire_patched_owserver_integration,
    setup_onewire_sysbus_integration,
    setup_owproxy_mock_devices,
)

from tests.common import MockConfigEntry, mock_device_registry, mock_registry


async def test_owserver_connect_failure(opp):
    """Test connection failure raises ConfigEntryNotReady."""
    config_entry_owserver = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_TYPE: CONF_TYPE_OWSERVER,
            CONF_HOST: "1.2.3.4",
            CONF_PORT: "1234",
        },
        options={},
        entry_id="2",
    )
    config_entry_owserver.add_to_opp(opp)

    with patch(
        "openpeerpower.components.onewire.onewirehub.protocol.proxy",
        side_effect=ConnError,
    ):
        await opp.config_entries.async_setup(config_entry_owserver.entry_id)
        await opp.async_block_till_done()

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert config_entry_owserver.state is ConfigEntryState.SETUP_RETRY
    assert not opp.data.get(DOMAIN)


async def test_failed_owserver_listing(opp):
    """Create the 1-Wire integration."""
    config_entry_owserver = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_TYPE: CONF_TYPE_OWSERVER,
            CONF_HOST: "1.2.3.4",
            CONF_PORT: "1234",
        },
        options={},
        entry_id="2",
    )
    config_entry_owserver.add_to_opp(opp)

    with patch("openpeerpower.components.onewire.onewirehub.protocol.proxy") as owproxy:
        owproxy.return_value.dir.side_effect = OwnetError
        await opp.config_entries.async_setup(config_entry_owserver.entry_id)
        await opp.async_block_till_done()

        return config_entry_owserver


async def test_unload_entry(opp):
    """Test being able to unload an entry."""
    config_entry_owserver = await setup_onewire_owserver_integration(opp)
    config_entry_sysbus = await setup_onewire_sysbus_integration(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 2
    assert config_entry_owserver.state is ConfigEntryState.LOADED
    assert config_entry_sysbus.state is ConfigEntryState.LOADED

    assert await opp.config_entries.async_unload(config_entry_owserver.entry_id)
    assert await opp.config_entries.async_unload(config_entry_sysbus.entry_id)
    await opp.async_block_till_done()

    assert config_entry_owserver.state is ConfigEntryState.NOT_LOADED
    assert config_entry_sysbus.state is ConfigEntryState.NOT_LOADED
    assert not opp.data.get(DOMAIN)


@patch("openpeerpower.components.onewire.onewirehub.protocol.proxy")
async def test_registry_cleanup(owproxy, opp):
    """Test for 1-Wire device.

    As they would be on a clean setup: all binary-sensors and switches disabled.
    """
    await async_setup_component(opp, "persistent_notification", {})
    entity_registry = mock_registry(opp)
    device_registry = mock_device_registry(opp)

    # Initialise with two components
    setup_owproxy_mock_devices(
        owproxy, SENSOR_DOMAIN, ["10.111111111111", "28.111111111111"]
    )
    with patch("openpeerpower.components.onewire.PLATFORMS", [SENSOR_DOMAIN]):
        await setup_onewire_patched_owserver_integration(opp)
        await opp.async_block_till_done()

    assert len(dr.async_entries_for_config_entry(device_registry, "2")) == 2
    assert len(er.async_entries_for_config_entry(entity_registry, "2")) == 2

    # Second item has disappeared from bus, and was removed manually from the front-end
    setup_owproxy_mock_devices(owproxy, SENSOR_DOMAIN, ["10.111111111111"])
    entity_registry.async_remove("sensor.28_111111111111_temperature")
    await opp.async_block_till_done()

    assert len(er.async_entries_for_config_entry(entity_registry, "2")) == 1
    assert len(dr.async_entries_for_config_entry(device_registry, "2")) == 2

    # Second item has disappeared from bus, and was removed manually from the front-end
    with patch("openpeerpower.components.onewire.PLATFORMS", [SENSOR_DOMAIN]):
        await opp.config_entries.async_reload("2")
        await opp.async_block_till_done()

    assert len(er.async_entries_for_config_entry(entity_registry, "2")) == 1
    assert len(dr.async_entries_for_config_entry(device_registry, "2")) == 1
