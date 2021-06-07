"""deCONZ service tests."""
from unittest.mock import Mock, patch

import pytest
import voluptuous as vol

from openpeerpower.components.deconz.const import (
    CONF_BRIDGE_ID,
    DOMAIN as DECONZ_DOMAIN,
)
from openpeerpower.components.deconz.deconz_event import CONF_DECONZ_EVENT
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
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.helpers.entity_registry import async_entries_for_config_entry

from .test_gateway import (
    BRIDGEID,
    DECONZ_WEB_REQUEST,
    mock_deconz_put_request,
    mock_deconz_request,
    setup_deconz_integration,
)

from tests.common import async_capture_events


async def test_service_setup(opp):
    """Verify service setup works."""
    assert DECONZ_SERVICES not in opp.data
    with patch(
        "openpeerpower.core.ServiceRegistry.async_register", return_value=Mock(True)
    ) as async_register:
        await async_setup_services(opp)
        assert opp.data[DECONZ_SERVICES] is True
        assert async_register.call_count == 3


async def test_service_setup_already_registered(opp):
    """Make sure that services are only registered once."""
    opp.data[DECONZ_SERVICES] = True
    with patch(
        "openpeerpower.core.ServiceRegistry.async_register", return_value=Mock(True)
    ) as async_register:
        await async_setup_services(opp)
        async_register.assert_not_called()


async def test_service_unload(opp):
    """Verify service unload works."""
    opp.data[DECONZ_SERVICES] = True
    with patch(
        "openpeerpower.core.ServiceRegistry.async_remove", return_value=Mock(True)
    ) as async_remove:
        await async_unload_services(opp)
        assert opp.data[DECONZ_SERVICES] is False
        assert async_remove.call_count == 3


async def test_service_unload_not_registered(opp):
    """Make sure that services can only be unloaded once."""
    with patch(
        "openpeerpower.core.ServiceRegistry.async_remove", return_value=Mock(True)
    ) as async_remove:
        await async_unload_services(opp)
        assert DECONZ_SERVICES not in opp.data
        async_remove.assert_not_called()


async def test_configure_service_with_field(opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)

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


async def test_configure_service_with_entity(opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    data = {
        "lights": {
            "1": {
                "name": "Test",
                "state": {"reachable": True},
                "type": "Light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    data = {
        SERVICE_ENTITY: "light.test",
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1")

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True, "attr1": 10, "attr2": 20}


async def test_configure_service_with_entity_and_field(opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    data = {
        "lights": {
            "1": {
                "name": "Test",
                "state": {"reachable": True},
                "type": "Light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

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


async def test_configure_service_with_faulty_field(opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz_integration(opp, aioclient_mock)

    data = {SERVICE_FIELD: "light/2", SERVICE_DATA: {}}

    with pytest.raises(vol.Invalid):
        await opp.services.async_call(
            DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data
        )
        await opp.async_block_till_done()


async def test_configure_service_with_faulty_entity(opp, aioclient_mock):
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz_integration(opp, aioclient_mock)
    aioclient_mock.clear_requests()

    data = {
        SERVICE_ENTITY: "light.nonexisting",
        SERVICE_DATA: {},
    }

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data
    )
    await opp.async_block_till_done()

    assert len(aioclient_mock.mock_calls) == 0


async def test_service_refresh_devices(opp, aioclient_mock):
    """Test that service can refresh devices."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert len(opp.states.async_all()) == 0

    aioclient_mock.clear_requests()

    data = {
        "groups": {
            "1": {
                "id": "Group 1 id",
                "name": "Group 1 name",
                "type": "LightGroup",
                "state": {},
                "action": {},
                "scenes": [{"id": "1", "name": "Scene 1"}],
                "lights": ["1"],
            }
        },
        "lights": {
            "1": {
                "name": "Light 1 name",
                "state": {"reachable": True},
                "type": "Light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
        "sensors": {
            "1": {
                "name": "Sensor 1 name",
                "type": "ZHALightLevel",
                "state": {"lightlevel": 30000, "dark": False},
                "config": {"reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:02-00",
            }
        },
    }

    mock_deconz_request(aioclient_mock, config_entry.data, data)

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_DEVICE_REFRESH, service_data={CONF_BRIDGE_ID: BRIDGEID}
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 4


async def test_service_refresh_devices_trigger_no_state_update(opp, aioclient_mock):
    """Verify that gateway.ignore_state_updates are honored."""
    data = {
        "sensors": {
            "1": {
                "name": "Switch 1",
                "type": "ZHASwitch",
                "state": {"buttonevent": 1000},
                "config": {"battery": 100},
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert len(opp.states.async_all()) == 1

    captured_events = async_capture_events(opp, CONF_DECONZ_EVENT)

    aioclient_mock.clear_requests()

    data = {
        "groups": {
            "1": {
                "id": "Group 1 id",
                "name": "Group 1 name",
                "type": "LightGroup",
                "state": {},
                "action": {},
                "scenes": [{"id": "1", "name": "Scene 1"}],
                "lights": ["1"],
            }
        },
        "lights": {
            "1": {
                "name": "Light 1 name",
                "state": {"reachable": True},
                "type": "Light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
        "sensors": {
            "1": {
                "name": "Switch 1",
                "type": "ZHASwitch",
                "state": {"buttonevent": 1000},
                "config": {"battery": 100},
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
    }

    mock_deconz_request(aioclient_mock, config_entry.data, data)

    await opp.services.async_call(
        DECONZ_DOMAIN, SERVICE_DEVICE_REFRESH, service_data={CONF_BRIDGE_ID: BRIDGEID}
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 4
    assert len(captured_events) == 0


async def test_remove_orphaned_entries_service(opp, aioclient_mock):
    """Test service works and also don't remove more than expected."""
    data = {
        "lights": {
            "1": {
                "name": "Light 1 name",
                "state": {"reachable": True},
                "type": "Light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
        "sensors": {
            "1": {
                "name": "Switch 1",
                "type": "ZHASwitch",
                "state": {"buttonevent": 1000, "gesture": 1},
                "config": {"battery": 100},
                "uniqueid": "00:00:00:00:00:00:00:03-00",
            },
        },
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry = await setup_deconz_integration(opp, aioclient_mock)

    device_registry = dr.async_get(opp)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "123")},
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

    entity_registry = er.async_get(opp)
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
        service_data={CONF_BRIDGE_ID: BRIDGEID},
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
