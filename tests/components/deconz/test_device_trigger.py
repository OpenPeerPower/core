"""deCONZ device automation tests."""

from copy import deepcopy

from openpeerpower.components.deconz import device_trigger
from openpeerpower.components.deconz.const import DOMAIN as DECONZ_DOMAIN
from openpeerpower.components.deconz.device_trigger import CONF_SUBTYPE
from openpeerpower.components.deconz.gateway import get_gateway_from_config_entry
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)

from .test_gateway import DECONZ_WEB_REQUEST, setup_deconz_integration

from tests.common import assert_lists_same, async_get_device_automations
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401

SENSORS = {
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
        CONF_TYPE: "ZHASwitch",
        "uniqueid": "d0:cf:5e:ff:fe:71:a4:3a-01-1000",
    }
}


async def test_get_triggers(opp, aioclient_mock):
    """Test triggers work."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)
    device_id = gateway.events[0].device_id
    triggers = await async_get_device_automations(opp, "trigger", device_id)

    expected_triggers = [
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_RELEASE,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DECONZ_DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_RELEASE,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: SENSOR_DOMAIN,
            ATTR_ENTITY_ID: "sensor.tradfri_on_off_switch_battery_level",
            CONF_PLATFORM: "device",
            CONF_TYPE: ATTR_BATTERY_LEVEL,
        },
    ]

    assert_lists_same(triggers, expected_triggers)


async def test_helper_successful(opp, aioclient_mock):
    """Verify trigger helper."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)
    device_id = gateway.events[0].device_id
    deconz_event = device_trigger._get_deconz_event_from_device_id(opp, device_id)
    assert deconz_event == gateway.events[0]


async def test_helper_no_match(opp, aioclient_mock):
    """Verify trigger helper returns None when no event could be matched."""
    await setup_deconz_integration(opp, aioclient_mock)
    deconz_event = device_trigger._get_deconz_event_from_device_id(opp, "mock-id")
    assert deconz_event is None


async def test_helper_no_gateway_exist(opp):
    """Verify trigger helper returns None when no gateway exist."""
    deconz_event = device_trigger._get_deconz_event_from_device_id(opp, "mock-id")
    assert deconz_event is None
