"""The tests for Climate device conditions."""
import pytest
import voluptuous_serialize

import openpeerpower.components.automation as automation
from openpeerpower.components.climate import DOMAIN, const, device_condition
from openpeerpower.helpers import config_validation as cv, device_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
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
    """Test we get the expected conditions from a climate."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set(
        f"{DOMAIN}.test_5678",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_MODE: const.HVAC_MODE_COOL,
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
    )
   .opp.states.async_set("climate.test_5678", "attributes", {"supported_features": 17})
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_hvac_mode",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_preset_mode",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    conditions = await async_get_device_automations.opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_get_conditions_hvac_only.opp, device_reg, entity_reg):
    """Test we get the expected conditions from a climate."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
   .opp.states.async_set(
        f"{DOMAIN}.test_5678",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_MODE: const.HVAC_MODE_COOL,
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
    )
   .opp.states.async_set("climate.test_5678", "attributes", {"supported_features": 1})
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "is_hvac_mode",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        }
    ]
    conditions = await async_get_device_automations.opp, "condition", device_entry.id)
    assert_lists_same(conditions, expected_conditions)


async def test_if_state.opp, calls):
    """Test for turn_on and turn_off conditions."""
   .opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_MODE: const.HVAC_MODE_COOL,
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
        },
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
                            "entity_id": "climate.entity",
                            "type": "is_hvac_mode",
                            "hvac_mode": "cool",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_hvac_mode - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                            "entity_id": "climate.entity",
                            "type": "is_preset_mode",
                            "preset_mode": "away",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "is_preset_mode - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                        },
                    },
                },
            ]
        },
    )
   .opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "is_hvac_mode - event - test_event1"

   .opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_AUTO,
        {
            const.ATTR_HVAC_MODE: const.HVAC_MODE_AUTO,
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
        },
    )

    # Should not fire
   .opp.bus.async_fire("test_event1")
    await opp.async_block_till_done()
    assert len(calls) == 1

   .opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()

    assert len(calls) == 2
    assert calls[1].data["some"] == "is_preset_mode - event - test_event2"

   .opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_AUTO,
        {
            const.ATTR_HVAC_MODE: const.HVAC_MODE_AUTO,
            const.ATTR_PRESET_MODE: const.PRESET_HOME,
        },
    )

    # Should not fire
   .opp.bus.async_fire("test_event2")
    await opp.async_block_till_done()
    assert len(calls) == 2


async def test_capabilities.opp):
    """Bla."""
   .opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_MODE: const.HVAC_MODE_COOL,
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
            const.ATTR_HVAC_MODES: [const.HVAC_MODE_COOL, const.HVAC_MODE_OFF],
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
    )

    # Test hvac mode
    capabilities = await device_condition.async_get_condition_capabilities(
        opp,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "",
            "entity_id": "climate.entity",
            "type": "is_hvac_mode",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "hvac_mode",
            "options": [("cool", "cool"), ("off", "off")],
            "required": True,
            "type": "select",
        }
    ]

    # Test preset mode
    capabilities = await device_condition.async_get_condition_capabilities(
        opp,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "",
            "entity_id": "climate.entity",
            "type": "is_preset_mode",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "preset_modes",
            "options": [("home", "home"), ("away", "away")],
            "required": True,
            "type": "select",
        }
    ]
