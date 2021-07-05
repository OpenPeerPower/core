"""Tests for the Mazda Connected Services integration."""
from datetime import timedelta
import json
from unittest.mock import patch

from pymazda import MazdaAuthenticationException, MazdaException
import pytest
import voluptuous as vol

from openpeerpower.components.mazda.const import DOMAIN, SERVICES
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    STATE_UNAVAILABLE,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import device_registry as dr
from openpeerpower.util import dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed, load_fixture
from tests.components.mazda import init_integration

FIXTURE_USER_INPUT = {
    CONF_EMAIL: "example@example.com",
    CONF_PASSWORD: "password",
    CONF_REGION: "MNAO",
}


async def test_config_entry_not_ready(opp: OpenPeerPower) -> None:
    """Test the Mazda configuration entry not ready."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        side_effect=MazdaException("Unknown error"),
    ):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_init_auth_failure(opp: OpenPeerPower):
    """Test auth failure during setup."""
    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Login failed"),
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
        config_entry.add_to_opp(opp)

        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.SETUP_ERROR

    flows = opp.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "user"


async def test_update_auth_failure(opp: OpenPeerPower):
    """Test auth failure during data update."""
    get_vehicles_fixture = json.loads(load_fixture("mazda/get_vehicles.json"))
    get_vehicle_status_fixture = json.loads(
        load_fixture("mazda/get_vehicle_status.json")
    )

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicles",
        return_value=get_vehicles_fixture,
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicle_status",
        return_value=get_vehicle_status_fixture,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
        config_entry.add_to_opp(opp)

        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicles",
        side_effect=MazdaAuthenticationException("Login failed"),
    ):
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=61))
        await opp.async_block_till_done()

    flows = opp.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "user"


async def test_update_general_failure(opp: OpenPeerPower):
    """Test general failure during data update."""
    get_vehicles_fixture = json.loads(load_fixture("mazda/get_vehicles.json"))
    get_vehicle_status_fixture = json.loads(
        load_fixture("mazda/get_vehicle_status.json")
    )

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicles",
        return_value=get_vehicles_fixture,
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicle_status",
        return_value=get_vehicle_status_fixture,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
        config_entry.add_to_opp(opp)

        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicles",
        side_effect=Exception("Unknown exception"),
    ):
        async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=61))
        await opp.async_block_till_done()

    entity = opp.states.get("sensor.my_mazda3_fuel_remaining_percentage")
    assert entity is not None
    assert entity.state == STATE_UNAVAILABLE


async def test_unload_config_entry(opp: OpenPeerPower) -> None:
    """Test the Mazda configuration entry unloading."""
    await init_integration(opp)
    assert opp.data[DOMAIN]

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state is ConfigEntryState.LOADED

    await opp.config_entries.async_unload(entries[0].entry_id)
    await opp.async_block_till_done()
    assert entries[0].state is ConfigEntryState.NOT_LOADED


async def test_device_nickname(opp):
    """Test creation of the device when vehicle has a nickname."""
    await init_integration(opp, use_nickname=True)

    device_registry = dr.async_get(opp)
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )

    assert reg_device.model == "2021 MAZDA3 2.5 S SE AWD"
    assert reg_device.manufacturer == "Mazda"
    assert reg_device.name == "My Mazda3"


async def test_device_no_nickname(opp):
    """Test creation of the device when vehicle has no nickname."""
    await init_integration(opp, use_nickname=False)

    device_registry = dr.async_get(opp)
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )

    assert reg_device.model == "2021 MAZDA3 2.5 S SE AWD"
    assert reg_device.manufacturer == "Mazda"
    assert reg_device.name == "2021 MAZDA3 2.5 S SE AWD"


async def test_services(opp):
    """Test service calls."""
    client_mock = await init_integration(opp)

    device_registry = dr.async_get(opp)
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )
    device_id = reg_device.id

    for service in SERVICES:
        service_data = {"device_id": device_id}
        if service == "send_poi":
            service_data["latitude"] = 1.2345
            service_data["longitude"] = 2.3456
            service_data["poi_name"] = "Work"

        await opp.services.async_call(DOMAIN, service, service_data, blocking=True)
        await opp.async_block_till_done()

        api_method = getattr(client_mock, service)
        if service == "send_poi":
            api_method.assert_called_once_with(12345, 1.2345, 2.3456, "Work")
        else:
            api_method.assert_called_once_with(12345)


async def test_service_invalid_device_id(opp):
    """Test service call when the specified device ID is invalid."""
    await init_integration(opp)

    with pytest.raises(vol.error.MultipleInvalid) as err:
        await opp.services.async_call(
            DOMAIN, "start_engine", {"device_id": "invalid"}, blocking=True
        )
        await opp.async_block_till_done()

    assert "Invalid device ID" in str(err.value)


async def test_service_device_id_not_mazda_vehicle(opp):
    """Test service call when the specified device ID is not the device ID of a Mazda vehicle."""
    await init_integration(opp)

    device_registry = dr.async_get(opp)
    # Create another device and pass its device ID.
    # Service should fail because device is from wrong domain.
    other_device = device_registry.async_get_or_create(
        config_entry_id="test_config_entry_id",
        identifiers={("OTHER_INTEGRATION", "ID_FROM_OTHER_INTEGRATION")},
    )

    with pytest.raises(vol.error.MultipleInvalid) as err:
        await opp.services.async_call(
            DOMAIN, "start_engine", {"device_id": other_device.id}, blocking=True
        )
        await opp.async_block_till_done()

    assert "Device ID is not a Mazda vehicle" in str(err.value)


async def test_service_vehicle_id_not_found(opp):
    """Test service call when the vehicle ID is not found."""
    await init_integration(opp)

    device_registry = dr.async_get(opp)
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )
    device_id = reg_device.id

    entries = opp.config_entries.async_entries(DOMAIN)
    entry_id = entries[0].entry_id

    # Remove vehicle info from opp.data so that vehicle ID will not be found
    opp.data[DOMAIN][entry_id]["vehicles"] = []

    with pytest.raises(OpenPeerPowerError) as err:
        await opp.services.async_call(
            DOMAIN, "start_engine", {"device_id": device_id}, blocking=True
        )
        await opp.async_block_till_done()

    assert str(err.value) == "Vehicle ID not found"


async def test_service_mazda_api_error(opp):
    """Test the Mazda API raising an error when a service is called."""
    get_vehicles_fixture = json.loads(load_fixture("mazda/get_vehicles.json"))
    get_vehicle_status_fixture = json.loads(
        load_fixture("mazda/get_vehicle_status.json")
    )

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicles",
        return_value=get_vehicles_fixture,
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicle_status",
        return_value=get_vehicle_status_fixture,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
        config_entry.add_to_opp(opp)

        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    device_registry = dr.async_get(opp)
    reg_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "JM000000000000000")},
    )
    device_id = reg_device.id

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.start_engine",
        side_effect=MazdaException("Test error"),
    ), pytest.raises(OpenPeerPowerError) as err:
        await opp.services.async_call(
            DOMAIN, "start_engine", {"device_id": device_id}, blocking=True
        )
        await opp.async_block_till_done()

    assert str(err.value) == "Test error"
