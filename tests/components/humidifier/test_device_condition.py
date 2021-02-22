"""The tests for Humidifier device conditions."""
import pytest
import voluptuous_serialize

import openpeerpower.components.automation as automation
from openpeerpower.components.humidifier import DOMAIN, const, device_condition
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.helpers import config_validation as cv, device_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def device_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry.opp)


@pytest.fixture
def entity_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_registry.opp)


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


async def test_get_conditions.opp, device_reg, entity_reg):
    """Test we get the expected conditions from a humidifier."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set(
        f"{DOMAIN}.test_5678",
        STATE_ON,
        {
            const.ATTR_MODE: const.MODE_AWAY,
            const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY],
        },
    )
   .opp.states.async_set(
        "humidifier.test_5678", "attributes", {"supported_features": 1}
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_off",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_on",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_mode",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    conditions = await async_get_device_automations.opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_get_conditions_toggle_only.opp, device_reg, entity_reg):
    """Test we get the expected conditions from a humidifier."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set(
        f"{DOMAIN}.test_5678",
        STATE_ON,
        {
            const.ATTR_MODE: const.MODE_AWAY,
            const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY],
        },
    )
   .opp.states.async_set(
        "humidifier.test_5678", "attributes", {"supported_features": 0}
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_off",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_on",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    conditions = await async_get_device_automations.opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_if_state.opp, calls):
    """Test for turn_on and turn_off conditions."""
   .opp.states.async_set(
        "humidifier.entity", STATE_ON, {const.ATTR_MODE: const.MODE_AWAY}
    )

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
                            "entity_id": "humidifier.entity",
                            "type": "is_on",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_on {{ trigger.%s }}"
                            % "}} - {{ trigger.".join(("platform", "event.event_type"))
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "humidifier.entity",
                            "type": "is_off",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_off {{ trigger.%s }}"
                            % "}} - {{ trigger.".join(("platform", "event.event_type"))
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": "humidifier.entity",
                            "type": "is_mode",
                            "mode": "away",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_mode - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()
    assert.opp.states.get("humidifier.entity").state == STATE_ON
    assert len(calls) == 0

   .opp.bus.async_fire("test_event1")
   .opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "is_on event - test_event1"

   .opp.states.async_set("humidifier.entity", STATE_OFF)
   .opp.bus.async_fire("test_event1")
   .opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "is_off event - test_event2"

   .opp.states.async_set(
        "humidifier.entity", STATE_ON, {const.ATTR_MODE: const.MODE_AWAY}
    )

   .opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()

    assert len(calls) == 3
    assert calls[2].data["some"] == "is_mode - event - test_event3"

   .opp.states.async_set(
        "humidifier.entity", STATE_ON, {const.ATTR_MODE: const.MODE_HOME}
    )

    # Should not fire
   .opp.bus.async_fire("test_event3")
    await opp.async_block_till_done()
    assert len(calls) == 3


async def test_capabilities.opp):
    """Test capabilities."""
   .opp.states.async_set(
        "humidifier.entity",
        STATE_ON,
        {
            const.ATTR_MODE: const.MODE_AWAY,
            const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY],
        },
    )

    # Test mode
    capabilities = await device_condition.async_get_condition_capabilities(
        opp,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "",
            "entity_id": "humidifier.entity",
            "type": "is_mode",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "available_modes",
            "options": [("home", "home"), ("away", "away")],
            "required": True,
            "type": "select",
        }
    ]


async def test_capabilities_no_state.opp):
    """Test capabilities while state not available."""
    # Test mode
    capabilities = await device_condition.async_get_condition_capabilities(
        opp,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "",
            "entity_id": "humidifier.entity",
            "type": "is_mode",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {"name": "available_modes", "options": [], "required": True, "type": "select"}
    ]


async def test_get_condition_capabilities.opp, device_reg, entity_reg):
    """Test we get the expected toggle capabilities."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    expected_capabilities = {
        "extra_fields": [
            {"name": "for", "optional": True, "type": "positive_time_period_dict"}
        ]
    }
    conditions = await async_get_device_automations.opp, "condition", device_entry.id)
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "condition", condition
        )
        assert capabilities == expected_capabilities
