"""deCONZ device automation tests."""

from unittest.mock import Mock, patch

import pytest

from openpeerpower.components.automation import DOMAIN as AUTOMATION_DOMAIN
from openpeerpower.components.deconz import device_trigger
from openpeerpower.components.deconz.const import DOMAIN as DECONZ_DOMAIN
from openpeerpower.components.deconz.device_trigger import CONF_SUBTYPE
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)
from openpeerpower.helpers.trigger import async_initialize_triggers
from openpeerpower.setup import async_setup_component

from .test_gateway import DECONZ_WEB_REQUEST, setup_deconz_integration

from tests.common import (
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401


@pytest.fixture
def automation_calls(opp):
    """Track automation calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_triggers(opp, aioclient_mock):
    """Test triggers work."""
    data = {
        "sensors": {
            "1": {
                "config": {
                    "alert": "none",
                    "battery": 60,
                    "group": "10",
                    "on": True,
                    "reachable": True,
                },
                "ep": 1,
                "etag": "1b355c0b6d2af28febd7ca9165881952",
                "manufacturername": "IKEA of Sweden",
                "mode": 1,
                "modelid": "TRADFRI on/off switch",
                "name": "TRÅDFRI on/off switch ",
                "state": {"buttonevent": 2002, "lastupdated": "2019-09-07T07:39:39"},
                "swversion": "1.4.018",
                "type": "ZHASwitch",
                "uniqueid": "d0:cf:5e:ff:fe:71:a4:3a-01-1000",
            }
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        await setup_deconz_integration(opp, aioclient_mock)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(
        identifiers={(DECONZ_DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")}
    )

    triggers = await async_get_device_automations(opp, "trigger", device.id)

    expected_triggers = [
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_RELEASE,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_RELEASE,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: SENSOR_DOMAIN,
            ATTR_ENTITY_ID: "sensor.tradfri_on_off_switch_battery_level",
            CONF_PLATFORM: "device",
            CONF_TYPE: ATTR_BATTERY_LEVEL,
        },
    ]

    assert_lists_same(triggers, expected_triggers)


async def test_get_triggers_manage_unsupported_remotes(opp, aioclient_mock):
    """Verify no triggers for an unsupported remote."""
    data = {
        "sensors": {
            "1": {
                "config": {
                    "alert": "none",
                    "group": "10",
                    "on": True,
                    "reachable": True,
                },
                "ep": 1,
                "etag": "1b355c0b6d2af28febd7ca9165881952",
                "manufacturername": "IKEA of Sweden",
                "mode": 1,
                "modelid": "Unsupported model",
                "name": "TRÅDFRI on/off switch ",
                "state": {"buttonevent": 2002, "lastupdated": "2019-09-07T07:39:39"},
                "swversion": "1.4.018",
                "type": "ZHASwitch",
                "uniqueid": "d0:cf:5e:ff:fe:71:a4:3a-01-1000",
            }
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        await setup_deconz_integration(opp, aioclient_mock)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(
        identifiers={(DECONZ_DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")}
    )

    triggers = await async_get_device_automations(opp, "trigger", device.id)

    expected_triggers = []

    assert_lists_same(triggers, expected_triggers)


async def test_functional_device_trigger(
    opp, aioclient_mock, mock_deconz_websocket, automation_calls
):
    """Test proper matching and attachment of device trigger automation."""
    await async_setup_component(opp, "persistent_notification", {})

    data = {
        "sensors": {
            "1": {
                "config": {
                    "alert": "none",
                    "battery": 60,
                    "group": "10",
                    "on": True,
                    "reachable": True,
                },
                "ep": 1,
                "etag": "1b355c0b6d2af28febd7ca9165881952",
                "manufacturername": "IKEA of Sweden",
                "mode": 1,
                "modelid": "TRADFRI on/off switch",
                "name": "TRÅDFRI on/off switch ",
                "state": {"buttonevent": 2002, "lastupdated": "2019-09-07T07:39:39"},
                "swversion": "1.4.018",
                "type": "ZHASwitch",
                "uniqueid": "d0:cf:5e:ff:fe:71:a4:3a-01-1000",
            }
        }
    }
    with patch.dict(DECONZ_WEB_REQUEST, data):
        await setup_deconz_integration(opp, aioclient_mock)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_device(
        identifiers={(DECONZ_DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")}
    )

    assert await async_setup_component(
        opp,
        AUTOMATION_DOMAIN,
        {
            AUTOMATION_DOMAIN: [
                {
                    "trigger": {
                        CONF_PLATFORM: "device",
                        CONF_DOMAIN: DECONZ_DOMAIN,
                        CONF_DEVICE_ID: device.id,
                        CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
                        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "test_trigger_button_press"},
                    },
                },
            ]
        },
    )

    assert len(opp.states.async_entity_ids(AUTOMATION_DOMAIN)) == 1

    event_changed_sensor = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "state": {"buttonevent": 1002},
    }
    await mock_deconz_websocket(data=event_changed_sensor)
    await opp.async_block_till_done()

    assert len(automation_calls) == 1
    assert automation_calls[0].data["some"] == "test_trigger_button_press"


async def test_validate_trigger_unknown_device(
    opp, aioclient_mock, mock_deconz_websocket
):
    """Test unknown device does not return a trigger config."""
    await setup_deconz_integration(opp, aioclient_mock)

    assert await async_setup_component(
        opp,
        AUTOMATION_DOMAIN,
        {
            AUTOMATION_DOMAIN: [
                {
                    "trigger": {
                        CONF_PLATFORM: "device",
                        CONF_DOMAIN: DECONZ_DOMAIN,
                        CONF_DEVICE_ID: "unknown device",
                        CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
                        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "test_trigger_button_press"},
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_entity_ids(AUTOMATION_DOMAIN)) == 0


async def test_validate_trigger_unsupported_device(
    opp, aioclient_mock, mock_deconz_websocket
):
    """Test unsupported device doesn't return a trigger config."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DECONZ_DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")},
        model="unsupported",
    )

    assert await async_setup_component(
        opp,
        AUTOMATION_DOMAIN,
        {
            AUTOMATION_DOMAIN: [
                {
                    "trigger": {
                        CONF_PLATFORM: "device",
                        CONF_DOMAIN: DECONZ_DOMAIN,
                        CONF_DEVICE_ID: device.id,
                        CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
                        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "test_trigger_button_press"},
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_entity_ids(AUTOMATION_DOMAIN)) == 0


async def test_validate_trigger_unsupported_trigger(
    opp, aioclient_mock, mock_deconz_websocket
):
    """Test unsupported trigger does not return a trigger config."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DECONZ_DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")},
        model="TRADFRI on/off switch",
    )

    trigger_config = {
        CONF_PLATFORM: "device",
        CONF_DOMAIN: DECONZ_DOMAIN,
        CONF_DEVICE_ID: device.id,
        CONF_TYPE: "unsupported",
        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
    }

    assert await async_setup_component(
        opp,
        AUTOMATION_DOMAIN,
        {
            AUTOMATION_DOMAIN: [
                {
                    "trigger": trigger_config,
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "test_trigger_button_press"},
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_entity_ids(AUTOMATION_DOMAIN)) == 0


async def test_attach_trigger_no_matching_event(
    opp, aioclient_mock, mock_deconz_websocket
):
    """Test no matching event for device doesn't return a trigger config."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)

    device_registry = await opp.helpers.device_registry.async_get_registry()
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DECONZ_DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")},
        name="Tradfri switch",
        model="TRADFRI on/off switch",
    )

    trigger_config = {
        CONF_PLATFORM: "device",
        CONF_DOMAIN: DECONZ_DOMAIN,
        CONF_DEVICE_ID: device.id,
        CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
    }

    assert await async_setup_component(
        opp,
        AUTOMATION_DOMAIN,
        {
            AUTOMATION_DOMAIN: [
                {
                    "trigger": trigger_config,
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "test_trigger_button_press"},
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_entity_ids(AUTOMATION_DOMAIN)) == 1

    # Assert that deCONZ async_attach_trigger raises InvalidDeviceAutomationConfig
    assert not await async_initialize_triggers(
        opp,
        [trigger_config],
        action=Mock(),
        domain=AUTOMATION_DOMAIN,
        name="mock-name",
        log_cb=Mock(),
    )
