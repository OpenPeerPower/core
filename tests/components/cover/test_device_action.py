"""The tests for Cover device actions."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.cover import DOMAIN
from openpeerpower.const import CONF_PLATFORM
from openpeerpowerr.helpers import device_registry
from openpeerpowerr.setup import async_setup_component

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


async def test_get_actions.opp, device_reg, entity_reg):
    """Test we get the expected actions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[0]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "open",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "close",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "stop",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_actions_tilt.opp, device_reg, entity_reg):
    """Test we get the expected actions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[3]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "open",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "close",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "stop",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "open_tilt",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "close_tilt",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_actions_set_pos.opp, device_reg, entity_reg):
    """Test we get the expected actions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[1]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "set_position",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_actions_set_tilt_pos.opp, device_reg, entity_reg):
    """Test we get the expected actions from a cover."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[2]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "open",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "close",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "stop",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
        {
            "domain": DOMAIN,
            "type": "set_tilt_position",
            "device_id": device_entry.id,
            "entity_id": ent.entity_id,
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_action_capabilities.opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a cover action."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[0]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert len(actions) == 3  # open, close, stop
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
           .opp, "action", action
        )
        assert capabilities == {"extra_fields": []}


async def test_get_action_capabilities_set_pos.opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a cover action."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[1]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "position",
                "optional": True,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            }
        ]
    }
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert len(actions) == 1  # set_position
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
           .opp, "action", action
        )
        if action["type"] == "set_position":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}


async def test_get_action_capabilities_set_tilt_pos.opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a cover action."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    ent = platform.ENTITIES[2]

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp..async_block_till_done()

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "position",
                "optional": True,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            }
        ]
    }
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert len(actions) == 4  # open, close, stop, set_tilt_position
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
           .opp, "action", action
        )
        if action["type"] == "set_tilt_position":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}


async def test_action.opp):
    """Test for cover actions."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event_open"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "open",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_close"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "close",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_stop"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "stop",
                    },
                },
            ]
        },
    )
    await opp..async_block_till_done()

    open_calls = async_mock_service.opp, "cover", "open_cover")
    close_calls = async_mock_service.opp, "cover", "close_cover")
    stop_calls = async_mock_service.opp, "cover", "stop_cover")

   .opp.bus.async_fire("test_event_open")
    await opp..async_block_till_done()
    assert len(open_calls) == 1
    assert len(close_calls) == 0
    assert len(stop_calls) == 0

   .opp.bus.async_fire("test_event_close")
    await opp..async_block_till_done()
    assert len(open_calls) == 1
    assert len(close_calls) == 1
    assert len(stop_calls) == 0

   .opp.bus.async_fire("test_event_stop")
    await opp..async_block_till_done()
    assert len(open_calls) == 1
    assert len(close_calls) == 1
    assert len(stop_calls) == 1


async def test_action_tilt.opp):
    """Test for cover tilt actions."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event_open"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "open_tilt",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_close"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "close_tilt",
                    },
                },
            ]
        },
    )
    await opp..async_block_till_done()

    open_calls = async_mock_service.opp, "cover", "open_cover_tilt")
    close_calls = async_mock_service.opp, "cover", "close_cover_tilt")

   .opp.bus.async_fire("test_event_open")
    await opp..async_block_till_done()
    assert len(open_calls) == 1
    assert len(close_calls) == 0

   .opp.bus.async_fire("test_event_close")
    await opp..async_block_till_done()
    assert len(open_calls) == 1
    assert len(close_calls) == 1

   .opp.bus.async_fire("test_event_stop")
    await opp..async_block_till_done()
    assert len(open_calls) == 1
    assert len(close_calls) == 1


async def test_action_set_position.opp):
    """Test for cover set position actions."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_pos",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "set_position",
                        "position": 25,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_tilt_pos",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "cover.entity",
                        "type": "set_tilt_position",
                        "position": 75,
                    },
                },
            ]
        },
    )
    await opp..async_block_till_done()

    cover_pos_calls = async_mock_service.opp, "cover", "set_cover_position")
    tilt_pos_calls = async_mock_service.opp, "cover", "set_cover_tilt_position")

   .opp.bus.async_fire("test_event_set_pos")
    await opp..async_block_till_done()
    assert len(cover_pos_calls) == 1
    assert cover_pos_calls[0].data["position"] == 25
    assert len(tilt_pos_calls) == 0

   .opp.bus.async_fire("test_event_set_tilt_pos")
    await opp..async_block_till_done()
    assert len(cover_pos_calls) == 1
    assert len(tilt_pos_calls) == 1
    assert tilt_pos_calls[0].data["tilt_position"] == 75
