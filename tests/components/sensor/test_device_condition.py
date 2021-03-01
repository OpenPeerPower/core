"""The test for sensor device automation."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.sensor import DOMAIN
from openpeerpower.components.sensor.device_condition import ENTITY_CONDITIONS
from openpeerpower.const import CONF_PLATFORM, PERCENTAGE, STATE_UNKNOWN
from openpeerpower.helpers import device_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa
from tests.testing_config.custom_components.test.sensor import DEVICE_CLASSES


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_conditions(opp, device_reg, entity_reg):
    """Test we get the expected conditions from a sensor."""
    platform = getattr(opp.components, f"test.{DOMAIN}")
    platform.init()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    for device_class in DEVICE_CLASSES:
        entity_reg.async_get_or_create(
            DOMAIN,
            "test",
            platform.ENTITIES[device_class].unique_id,
            device_id=device_entry.id,
        )

    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition["type"],
            "device_id": device_entry.id,
            "entity_id": platform.ENTITIES[device_class].entity_id,
        }
        for device_class in DEVICE_CLASSES
        for condition in ENTITY_CONDITIONS[device_class]
        if device_class != "none"
    ]
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert conditions == expected_conditions


async def test_get_condition_capabilities(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a sensor condition."""
    platform = getattr(opp.components, f"test.{DOMAIN}")
    platform.init()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        platform.ENTITIES["battery"].unique_id,
        device_id=device_entry.id,
    )

    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    expected_capabilities = {
        "extra_fields": [
            {
                "description": {"suffix": PERCENTAGE},
                "name": "above",
                "optional": True,
                "type": "float",
            },
            {
                "description": {"suffix": PERCENTAGE},
                "name": "below",
                "optional": True,
                "type": "float",
            },
        ]
    }
    conditions = await async_get_device_automations(opp, "condition", device_entry.id)
    assert len(conditions) == 1
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "condition", condition
        )
        assert capabilities == expected_capabilities


async def test_get_condition_capabilities_none(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a sensor condition."""
    platform = getattr(opp.components, f"test.{DOMAIN}")
    platform.init()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)

    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    conditions = [
        {
            "condition": "device",
            "device_id": "8770c43885354d5fa27604db6817f63f",
            "domain": "sensor",
            "entity_id": "sensor.beer",
            "type": "is_battery_level",
        },
        {
            "condition": "device",
            "device_id": "8770c43885354d5fa27604db6817f63f",
            "domain": "sensor",
            "entity_id": platform.ENTITIES["none"].entity_id,
            "type": "is_battery_level",
        },
    ]

    expected_capabilities = {}
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "condition", condition
        )
        assert capabilities == expected_capabilities


async def test_if_state_not_above_below(opp, calls, caplog):
    """Test for bad value conditions."""
    platform = getattr(opp.components, f"test.{DOMAIN}")

    platform.init()
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    sensor1 = platform.ENTITIES["battery"]

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": sensor1.entity_id,
                            "type": "is_battery_level",
                        }
                    ],
                    "action": {"service": "test.automation"},
                }
            ]
        },
    )
    assert "must contain at least one of below, above" in caplog.text


async def test_if_state_above(opp, calls):
    """Test for value conditions."""
    platform = getattr(opp.components, f"test.{DOMAIN}")

    platform.init()
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    sensor1 = platform.ENTITIES["battery"]

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": sensor1.entity_id,
                            "type": "is_battery_level",
                            "above": 10,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.%s }}"
                            % "}} - {{ trigger.".join(("platform", "event.event_type"))
                        },
                    },
                }
            ]
        },
    )
    await opp.async_block_till_done()
    assert opp.states.get(sensor1.entity_id).state == STATE_UNKNOWN
    assert len(calls) == 0

    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set(sensor1.entity_id, 9)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set(sensor1.entity_id, 11)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "event - test_event1"


async def test_if_state_below(opp, calls):
    """Test for value conditions."""
    platform = getattr(opp.components, f"test.{DOMAIN}")

    platform.init()
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    sensor1 = platform.ENTITIES["battery"]

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": sensor1.entity_id,
                            "type": "is_battery_level",
                            "below": 10,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.%s }}"
                            % "}} - {{ trigger.".join(("platform", "event.event_type"))
                        },
                    },
                }
            ]
        },
    )
    await opp.async_block_till_done()
    assert opp.states.get(sensor1.entity_id).state == STATE_UNKNOWN
    assert len(calls) == 0

    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set(sensor1.entity_id, 11)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set(sensor1.entity_id, 9)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "event - test_event1"


async def test_if_state_between(opp, calls):
    """Test for value conditions."""
    platform = getattr(opp.components, f"test.{DOMAIN}")

    platform.init()
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    sensor1 = platform.ENTITIES["battery"]

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": sensor1.entity_id,
                            "type": "is_battery_level",
                            "above": 10,
                            "below": 20,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.%s }}"
                            % "}} - {{ trigger.".join(("platform", "event.event_type"))
                        },
                    },
                }
            ]
        },
    )
    await opp.async_block_till_done()
    assert opp.states.get(sensor1.entity_id).state == STATE_UNKNOWN
    assert len(calls) == 0

    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set(sensor1.entity_id, 9)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 0

    opp.states.async_set(sensor1.entity_id, 11)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "event - test_event1"

    opp.states.async_set(sensor1.entity_id, 21)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 1

    opp.states.async_set(sensor1.entity_id, 19)
    opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "event - test_event1"
