"""deCONZ service tests."""

from copy import deepcopy
from unittest.mock import Mock, patch

import pytest
import voluptuous as vol

from openpeerpower.components.deconz.const import (
    CONF_BRIDGE_ID,
    DOMAIN as DECONZ_DOMAIN,
)
from openpeerpower.components.deconz.gateway import get_gateway_from_config_entry
from openpeerpower.components.deconz.services import (
    DECONZ_SERVICES,
    SERVICE_CONFIGURE_DEVICE,
    SERVICE_DATA,
    SERVICE_DEVICE_REFRESH,
    SERVICE_ENTITY,
    SERVICE_FIELD,
    SERVICE_REMOVE_ORPHANED_ENTRIES,
    async_setup_services,
    async_unload_services,
)
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.helpers.entity_registry import async_entries_for_config_entry

from .test_gateway import (
    BRIDGEID,
    DECONZ_WEB_REQUEST,
    mock_deconz_put_request,
    mock_deconz_request,
    setup_deconz_integration,
)

GROUP = {
    "1": {
        "id": "Group 1 id",
        "name": "Group 1 name",
        "type": "LightGroup",
        "state": {},
        "action": {},
        "scenes": [{"id": "1", "name": "Scene 1"}],
        "lights": ["1"],
    }
}

LIGHT = {
    "1": {
        "id": "Light 1 id",
        "name": "Light 1 name",
        "state": {"reachable": True},
        "type": "Light",
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    }
}

SENSOR = {
    "1": {
        "id": "Sensor 1 id",
        "name": "Sensor 1 name",
        "type": "ZHALightLevel",
        "state": {"lightlevel": 30000, "dark": False},
        "config": {"reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    }
}

SWITCH = {
    "1": {
        "id": "Switch 1 id",
        "name": "Switch 1",
        "type": "ZHASwitch",
        "state": {"buttonevent": 1000, "gesture": 1},
        "config": {"battery": 100},
        "uniqueid": "00:00:00:00:00:00:00:03-00",
    },
}


async def test_service_setup_opp):
    """Verify service setup works."""
    assert DECONZ_SERVICES not in.opp.data
    with patch(
        "openpeerpower.core.ServiceRegistry.async_register", return_value=Mock(True)
    ) as async_register:
        await async_setup_services.opp)
        assert.opp.data[DECONZ_SERVICES] is True
        assert async_register.call_count == 3


async def test_service_setup_already_registered.opp):
    """Make sure that services are only registered once."""
   .opp.data[DECONZ_SERVICES] = True
    with patch(
        "openpeerpower.core.ServiceRegistry.async_register", return_value=Mock(True)
    ) as async_register:
        await async_setup_services.opp)
        async_register.assert_not_called()


async def test_service_unload.opp):
    """Verify service unload works."""
   .opp.data[DECONZ_SERVICES] = True
    with patch(
        "openpeerpower.core.ServiceRegistry.async_remove", return_value=Mock(True)
    ) as async_remove:
        await async_unload_services.opp)
        assert.opp.data[DECONZ_SERVICES] is False
        assert async_remove.call_count == 3


async def test_service_unload_not_registered.opp):
    """Make sure that services can only be unloaded once."""
    with patch(
        "openpeerpower.core.ServiceRegistry.async_remove", return_value=Mock(True)
    ) as async_remove:
        await async_unload_services.opp)
        assert DECONZ_SERVICES not in.opp.data
        async_remove.assert_not_called()


async def test_configure_service_with_field.opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    config_entry = await setup_deconz_integration.opp, aioclient_mock)

    data = {
        SERVICE_FIELD: "/lights/2",
        CONF_BRIDGE_ID: BRIDGEID,
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/2")

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True, "attr1": 10, "attr2": 20}


async def test_configure_service_with_entity.opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    config_entry = await setup_deconz_integration.opp, aioclient_mock)
    gateway = get_gateway_from_config_entry.opp, config_entry)

    gateway.deconz_ids["light.test"] = "/lights/1"
    data = {
        SERVICE_ENTITY: "light.test",
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1")

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True, "attr1": 10, "attr2": 20}


async def test_configure_service_with_entity_and_field.opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    config_entry = await setup_deconz_integration.opp, aioclient_mock)
    gateway = get_gateway_from_config_entry.opp, config_entry)

    gateway.deconz_ids["light.test"] = "/lights/1"
    data = {
        SERVICE_ENTITY: "light.test",
        SERVICE_FIELD: "/state",
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True, "attr1": 10, "attr2": 20}


async def test_configure_service_with_faulty_field.opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz_integration.opp, aioclient_mock)

    data = {SERVICE_FIELD: "light/2", SERVICE_DATA: {}}

    with pytest.raises(vol.Invalid):
        await opp.services.async_call(
            DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data
        )
        await opp.async_block_till_done()


async def test_configure_service_with_faulty_entity.opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz_integration.opp, aioclient_mock)

    data = {
        SERVICE_ENTITY: "light.nonexisting",
        SERVICE_DATA: {},
    }

    with patch("pydeconz.DeconzSession.request", return_value=Mock(True)) as put_state:
        await opp.services.async_call(
            DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data
        )
        await opp.async_block_till_done()
        put_state.assert_not_called()


async def test_service_refresh_devices.opp, aioclient_mock):
    """Test that service can refresh devices."""
    config_entry = await setup_deconz_integration.opp, aioclient_mock)
    gateway = get_gateway_from_config_entry.opp, config_entry)
    aioclient_mock.clear_requests()

    data = {CONF_BRIDGE_ID: BRIDGEID}

    mock_deconz_request(
        aioclient_mock,
        config_entry.data,
        {"groups": GROUP, "lights": LIGHT, "sensors": SENSOR},
    )

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_DEVICE_REFRESH, service_data=data
    )
    await opp.async_block_till_done()

    assert gateway.deconz_ids == {
        "light.group_1_name": "/groups/1",
        "light.light_1_name": "/lights/1",
        "scene.group_1_name_scene_1": "/groups/1/scenes/1",
        "sensor.sensor_1_name": "/sensors/1",
    }


async def test_remove_orphaned_entries_service.opp, aioclient_mock):
    """Test service works and also don't remove more than expected."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["lights"] = deepcopy(LIGHT)
    data["sensors"] = deepcopy(SWITCH)
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )

    data = {CONF_BRIDGE_ID: BRIDGEID}

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id, identifiers={("mac", "123")}
    )

    assert (
        len(
            [
                entry
                for entry in device_registry.devices.values()
                if config_entry.entry_id in entry.config_entries
            ]
        )
        == 5  # Host, gateway, light, switch and orphan
    )

    entity_registry = await opp.helpers.entity_registry.async_get_registry()
    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DECONZ_DOMAIN,
        "12345",
        suggested_object_id="Orphaned sensor",
        config_entry=config_entry,
        device_id=device.id,
    )

    assert (
        len(async_entries_for_config_entry(entity_registry, config_entry.entry_id))
        == 3  # Light, switch battery and orphan
    )

    await opp.services.async_call(
        DECONZ_DOMAIN,
        SERVICE_REMOVE_ORPHANED_ENTRIES,
        service_data=data,
    )
    await opp.async_block_till_done()

    assert (
        len(
            [
                entry
                for entry in device_registry.devices.values()
                if config_entry.entry_id in entry.config_entries
            ]
        )
        == 4  # Host, gateway, light and switch
    )

    assert (
        len(async_entries_for_config_entry(entity_registry, config_entry.entry_id))
        == 2  # Light and switch battery
    )
