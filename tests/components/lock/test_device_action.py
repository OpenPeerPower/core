"""The tests for Lock device actions."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.lock import DOMAIN
from openpeerpower.const import CONF_PLATFORM
from openpeerpowerr.helpers import device_registry
from openpeerpowerr.setup import async_setup_component

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


async def test_get_actions_support_open.opp, device_reg, entity_reg):
    """Test we get the expected actions from a lock which supports open."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        platform.ENTITIES["support_open"].unique_id,
        device_id=device_entry.id,
    )

    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "lock",
            "device_id": device_entry.id,
            "entity_id": "lock.support_open_lock",
        },
        {
            "domain": DOMAIN,
            "type": "unlock",
            "device_id": device_entry.id,
            "entity_id": "lock.support_open_lock",
        },
        {
            "domain": DOMAIN,
            "type": "open",
            "device_id": device_entry.id,
            "entity_id": "lock.support_open_lock",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_get_actions_not_support_open.opp, device_reg, entity_reg):
    """Test we get the expected actions from a lock which doesn't support open."""
    platform = getattr.opp.components, f"test.{DOMAIN}")
    platform.init()
    assert await async_setup_component.opp, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await opp.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(
        DOMAIN,
        "test",
        platform.ENTITIES["no_support_open"].unique_id,
        device_id=device_entry.id,
    )

    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "lock",
            "device_id": device_entry.id,
            "entity_id": "lock.no_support_open_lock",
        },
        {
            "domain": DOMAIN,
            "type": "unlock",
            "device_id": device_entry.id,
            "entity_id": "lock.no_support_open_lock",
        },
    ]
    actions = await async_get_device_automations.opp, "action", device_entry.id)
    assert_lists_same(actions, expected_actions)


async def test_action.opp):
    """Test for lock actions."""
    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event_lock"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "lock.entity",
                        "type": "lock",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_unlock"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "lock.entity",
                        "type": "unlock",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_open"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": "abcdefgh",
                        "entity_id": "lock.entity",
                        "type": "open",
                    },
                },
            ]
        },
    )
    await opp.async_block_till_done()

    lock_calls = async_mock_service.opp, "lock", "lock")
    unlock_calls = async_mock_service.opp, "lock", "unlock")
    open_calls = async_mock_service.opp, "lock", "open")

   .opp.bus.async_fire("test_event_lock")
    await opp.async_block_till_done()
    assert len(lock_calls) == 1
    assert len(unlock_calls) == 0
    assert len(open_calls) == 0

   .opp.bus.async_fire("test_event_unlock")
    await opp.async_block_till_done()
    assert len(lock_calls) == 1
    assert len(unlock_calls) == 1
    assert len(open_calls) == 0

   .opp.bus.async_fire("test_event_open")
    await opp.async_block_till_done()
    assert len(lock_calls) == 1
    assert len(unlock_calls) == 1
    assert len(open_calls) == 1
