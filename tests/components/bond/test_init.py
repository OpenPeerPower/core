"""Tests for the Bond module."""
from unittest.mock import Mock

from aiohttp import ClientConnectionError, ClientResponseError
from bond_api import DeviceType

from openpeerpower.components.bond.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_ACCESS_TOKEN, CONF_HOST
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import device_registry as dr
from openpeerpower.setup import async_setup_component

from .common import (
    patch_bond_bridge,
    patch_bond_device,
    patch_bond_device_ids,
    patch_bond_device_properties,
    patch_bond_device_state,
    patch_bond_version,
    patch_setup_entry,
    patch_start_bpup,
    setup_bond_entity,
)

from tests.common import MockConfigEntry


async def test_async_setup_no_domain_config(opp: OpenPeerPower):
    """Test setup without configuration is noop."""
    result = await async_setup_component(opp, DOMAIN, {})

    assert result is True


async def test_async_setup_raises_entry_not_ready.opp: OpenPeerPower):
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )
    config_entry.add_to_opp(opp)

    with patch_bond_version(side_effect=ClientConnectionError()):
        await opp.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ENTRY_STATE_SETUP_RETRY


async def test_async_setup_entry_sets_up_hub_and_supported_domains.opp: OpenPeerPower):
    """Test that configuring entry sets up cover domain."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    with patch_bond_bridge(), patch_bond_version(
        return_value={
            "bondid": "test-bond-id",
            "target": "test-model",
            "fw_ver": "test-version",
        }
    ), patch_setup_entry("cover") as mock_cover_async_setup_entry, patch_setup_entry(
        "fan"
    ) as mock_fan_async_setup_entry, patch_setup_entry(
        "light"
    ) as mock_light_async_setup_entry, patch_setup_entry(
        "switch"
    ) as mock_switch_async_setup_entry:
        result = await setup_bond_entity(opp, config_entry, patch_device_ids=True)
        assert result is True
        await opp.async_block_till_done()

    assert config_entry.entry_id in.opp.data[DOMAIN]
    assert config_entry.state == ENTRY_STATE_LOADED
    assert config_entry.unique_id == "test-bond-id"

    # verify hub device is registered correctly
    device_registry = await dr.async_get_registry.opp)
    hub = device_registry.async_get_device(identifiers={(DOMAIN, "test-bond-id")})
    assert hub.name == "bond-name"
    assert hub.manufacturer == "Olibra"
    assert hub.model == "test-model"
    assert hub.sw_version == "test-version"

    # verify supported domains are setup
    assert len(mock_cover_async_setup_entry.mock_calls) == 1
    assert len(mock_fan_async_setup_entry.mock_calls) == 1
    assert len(mock_light_async_setup_entry.mock_calls) == 1
    assert len(mock_switch_async_setup_entry.mock_calls) == 1


async def test_unload_config_entry.opp: OpenPeerPower):
    """Test that configuration entry supports unloading."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    result = await setup_bond_entity(
        opp,
        config_entry,
        patch_version=True,
        patch_device_ids=True,
        patch_platforms=True,
        patch_bridge=True,
    )
    assert result is True
    await opp.async_block_till_done()

    await opp.config_entries.async_unload(config_entry.entry_id)
    await opp.async_block_till_done()

    assert config_entry.entry_id not in.opp.data[DOMAIN]
    assert config_entry.state == ENTRY_STATE_NOT_LOADED


async def test_old_identifiers_are_removed.opp: OpenPeerPower):
    """Test we remove the old non-unique identifiers."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    old_identifers = (DOMAIN, "device_id")
    new_identifiers = (DOMAIN, "test-bond-id", "device_id")
    device_registry = await opp.helpers.device_registry.async_get_registry()
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={old_identifers},
        manufacturer="any",
        name="old",
    )

    config_entry.add_to_opp(opp)

    with patch_bond_bridge(), patch_bond_version(
        return_value={
            "bondid": "test-bond-id",
            "target": "test-model",
            "fw_ver": "test-version",
        }
    ), patch_start_bpup(), patch_bond_device_ids(
        return_value=["bond-device-id", "device_id"]
    ), patch_bond_device(
        return_value={
            "name": "test1",
            "type": DeviceType.GENERIC_DEVICE,
        }
    ), patch_bond_device_properties(
        return_value={}
    ), patch_bond_device_state(
        return_value={}
    ):
        assert await opp.config_entries.async_setup(config_entry.entry_id) is True
        await opp.async_block_till_done()

    assert config_entry.entry_id in.opp.data[DOMAIN]
    assert config_entry.state == ENTRY_STATE_LOADED
    assert config_entry.unique_id == "test-bond-id"

    # verify the device info is cleaned up
    assert device_registry.async_get_device(identifiers={old_identifers}) is None
    assert device_registry.async_get_device(identifiers={new_identifiers}) is not None


async def test_smart_by_bond_device_suggested_area.opp: OpenPeerPower):
    """Test we can setup a smart by bond device and get the suggested area."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    config_entry.add_to_opp(opp)

    with patch_bond_bridge(
        side_effect=ClientResponseError(Mock(), Mock(), status=404)
    ), patch_bond_version(
        return_value={
            "bondid": "test-bond-id",
            "target": "test-model",
            "fw_ver": "test-version",
        }
    ), patch_start_bpup(), patch_bond_device_ids(
        return_value=["bond-device-id", "device_id"]
    ), patch_bond_device(
        return_value={
            "name": "test1",
            "type": DeviceType.GENERIC_DEVICE,
            "location": "Den",
        }
    ), patch_bond_device_properties(
        return_value={}
    ), patch_bond_device_state(
        return_value={}
    ):
        assert await opp.config_entries.async_setup(config_entry.entry_id) is True
        await opp.async_block_till_done()

    assert config_entry.entry_id in.opp.data[DOMAIN]
    assert config_entry.state == ENTRY_STATE_LOADED
    assert config_entry.unique_id == "test-bond-id"

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={(DOMAIN, "test-bond-id")})
    assert device is not None
    assert device.suggested_area == "Den"


async def test_bridge_device_suggested_area.opp: OpenPeerPower):
    """Test we can setup a bridge bond device and get the suggested area."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    config_entry.add_to_opp(opp)

    with patch_bond_bridge(
        return_value={
            "name": "Office Bridge",
            "location": "Office",
        }
    ), patch_bond_version(
        return_value={
            "bondid": "test-bond-id",
            "target": "test-model",
            "fw_ver": "test-version",
        }
    ), patch_start_bpup(), patch_bond_device_ids(
        return_value=["bond-device-id", "device_id"]
    ), patch_bond_device(
        return_value={
            "name": "test1",
            "type": DeviceType.GENERIC_DEVICE,
            "location": "Bathroom",
        }
    ), patch_bond_device_properties(
        return_value={}
    ), patch_bond_device_state(
        return_value={}
    ):
        assert await opp.config_entries.async_setup(config_entry.entry_id) is True
        await opp.async_block_till_done()

    assert config_entry.entry_id in.opp.data[DOMAIN]
    assert config_entry.state == ENTRY_STATE_LOADED
    assert config_entry.unique_id == "test-bond-id"

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(identifiers={(DOMAIN, "test-bond-id")})
    assert device is not None
    assert device.suggested_area == "Office"
