"""The test for light device automation."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.light import (
    DOMAIN,
    FLASH_LONG,
    FLASH_SHORT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_FLASH,
)
from openpeerpower.const import CONF_PLATFORM, STATE_OFF, STATE_ON
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


async def test_get_actions(opp, device_reg, entity_reg):
    """Test we get the expected actions from a light."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        supported_features=SUPPORT_BRIGHTNESS | SUPPORT_FLASH,
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "toggle",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "brightness_increase",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "brightness_decrease",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "domain": DOMAIN,
            "type": "flash",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    actions = await async_get_device_automations(opp, "action", device_entry.id)
    assert actions == expected_actions


async def test_get_action_capabilities(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
    )

    actions = await async_get_device_automations(opp, "action", device_entry.id)
    assert len(actions) == 3
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "action", action
        )
        assert capabilities == {"extra_fields": []}


async def test_get_action_capabilities_brightness(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        supported_features=SUPPORT_BRIGHTNESS,
    )

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "brightness_pct",
                "optional": True,
                "type": "float",
                "valueMax": 100,
                "valueMin": 0,
            }
        ]
    }
    actions = await async_get_device_automations(opp, "action", device_entry.id)
    assert len(actions) == 5
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "action", action
        )
        if action["type"] == "turn_on":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}


async def test_get_action_capabilities_flash(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        supported_features=SUPPORT_FLASH,
    )

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "flash",
                "optional": True,
                "type": "select",
                "options": [("short", "short"), ("long", "long")],
            }
        ]
    }

    actions = await async_get_device_automations(opp, "action", device_entry.id)
    assert len(actions) == 4
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            opp, "action", action
        )
        if action["type"] == "turn_on":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}


async def test_action(opp, calls):
    """Test for turn_on and turn_off actions."""
    platform = getattr(opp.components, f"test.{DOMAIN}")

    platform.init()
    assert await async_setup_component(opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    ent1, ent2, ent3 = platform.ENTITIES

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_off"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "turn_off",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_on"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "turn_on",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_toggle"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "toggle",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_flash_short"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "flash",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_flash_long"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "flash",
                        "flash": "long",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_brightness_increase",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "brightness_increase",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_brightness_decrease",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "brightness_decrease",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_brightness"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": ent1.entity_id,
                        "type": "turn_on",
                        "brightness_pct": 75,
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_ON
    assert len(calls) == 0

    opp.bus.async_fire("test_off")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_OFF

    opp.bus.async_fire("test_off")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_OFF

    opp.bus.async_fire("test_on")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_ON

    opp.bus.async_fire("test_on")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_ON

    opp.bus.async_fire("test_toggle")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_OFF

    opp.bus.async_fire("test_toggle")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_ON

    opp.bus.async_fire("test_toggle")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_OFF

    opp.bus.async_fire("test_flash_short")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_ON

    opp.bus.async_fire("test_toggle")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_OFF

    opp.bus.async_fire("test_flash_long")
    await opp.async_block_till_done()
    assert opp.states.get(ent1.entity_id).state == STATE_ON

    turn_on_calls = async_mock_service(opp, DOMAIN, "turn_on")

    opp.bus.async_fire("test_brightness_increase")
    await opp.async_block_till_done()

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].data["entity_id"] == ent1.entity_id
    assert turn_on_calls[0].data["brightness_step_pct"] == 10

    opp.bus.async_fire("test_brightness_decrease")
    await opp.async_block_till_done()

    assert len(turn_on_calls) == 2
    assert turn_on_calls[1].data["entity_id"] == ent1.entity_id
    assert turn_on_calls[1].data["brightness_step_pct"] == -10

    opp.bus.async_fire("test_brightness")
    await opp.async_block_till_done()

    assert len(turn_on_calls) == 3
    assert turn_on_calls[2].data["entity_id"] == ent1.entity_id
    assert turn_on_calls[2].data["brightness_pct"] == 75

    opp.bus.async_fire("test_on")
    await opp.async_block_till_done()

    assert len(turn_on_calls) == 4
    assert turn_on_calls[3].data["entity_id"] == ent1.entity_id
    assert "brightness_pct" not in turn_on_calls[3].data

    opp.bus.async_fire("test_flash_short")
    await opp.async_block_till_done()

    assert len(turn_on_calls) == 5
    assert turn_on_calls[4].data["entity_id"] == ent1.entity_id
    assert turn_on_calls[4].data["flash"] == FLASH_SHORT

    opp.bus.async_fire("test_flash_long")
    await opp.async_block_till_done()

    assert len(turn_on_calls) == 6
    assert turn_on_calls[5].data["entity_id"] == ent1.entity_id
    assert turn_on_calls[5].data["flash"] == FLASH_LONG
