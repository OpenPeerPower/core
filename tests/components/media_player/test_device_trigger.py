"""The tests for Media player device triggers."""
from datetime import timedelta

import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.media_player import DOMAIN
from openpeerpower.const import (
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from openpeerpower.helpers import device_registry
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_fire_time_changed,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401


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


async def test_get_triggers(opp, device_reg, entity_reg):
    """Test we get the expected triggers from a media player."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)

    trigger_types = {"turned_on", "turned_off", "idle", "paused", "playing"}
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        }
        for trigger in trigger_types
    ]
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers)


async def test_get_trigger_capabilities(opp, device_reg, entity_reg):
    """Test we get the expected capabilities from a media player."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)

    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert len(triggers) == 5
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            opp, "trigger", trigger
        )
        assert capabilities == {
            "extra_fields": [
                {"name": "for", "optional": True, "type": "positive_time_period_dict"}
            ]
        }


async def test_if_fires_on_state_change(opp, calls):
    """Test triggers firing."""
    opp.states.async_set("media_player.entity", STATE_OFF)

    data_template = (
        "{label} - {{{{ trigger.platform}}}} - "
        "{{{{ trigger.entity_id}}}} - {{{{ trigger.from_state.state}}}} - "
        "{{{{ trigger.to_state.state}}}} - {{{{ trigger.for }}}}"
    )
    trigger_types = {"turned_on", "turned_off", "idle", "paused", "playing"}

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": "media_player.entity",
                        "type": trigger,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": data_template.format(label=trigger)},
                    },
                }
                for trigger in trigger_types
            ]
        },
    )

    # Fake that the entity is turning on.
    opp.states.async_set("media_player.entity", STATE_ON)
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert (
        calls[0].data["some"]
        == "turned_on - device - media_player.entity - off - on - None"
    )

    # Fake that the entity is turning off.
    opp.states.async_set("media_player.entity", STATE_OFF)
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert (
        calls[1].data["some"]
        == "turned_off - device - media_player.entity - on - off - None"
    )

    # Fake that the entity becomes idle.
    opp.states.async_set("media_player.entity", STATE_IDLE)
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert (
        calls[2].data["some"]
        == "idle - device - media_player.entity - off - idle - None"
    )

    # Fake that the entity starts playing.
    opp.states.async_set("media_player.entity", STATE_PLAYING)
    await opp.async_block_till_done()
    assert len(calls) == 4
    assert (
        calls[3].data["some"]
        == "playing - device - media_player.entity - idle - playing - None"
    )

    # Fake that the entity is paused.
    opp.states.async_set("media_player.entity", STATE_PAUSED)
    await opp.async_block_till_done()
    assert len(calls) == 5
    assert (
        calls[4].data["some"]
        == "paused - device - media_player.entity - playing - paused - None"
    )


async def test_if_fires_on_state_change_with_for(opp, calls):
    """Test for triggers firing with delay."""
    entity_id = f"{DOMAIN}.entity"
    opp.states.async_set(entity_id, STATE_OFF)

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": entity_id,
                        "type": "turned_on",
                        "for": {"seconds": 5},
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "turn_off {{ trigger.%s }}"
                            % "}} - {{ trigger.".join(
                                (
                                    "platform",
                                    "entity_id",
                                    "from_state.state",
                                    "to_state.state",
                                    "for",
                                )
                            )
                        },
                    },
                }
            ]
        },
    )
    await opp.async_block_till_done()
    assert opp.states.get(entity_id).state == STATE_OFF
    assert len(calls) == 0

    opp.states.async_set(entity_id, STATE_ON)
    await opp.async_block_till_done()
    assert len(calls) == 0
    async_fire_time_changed(opp, dt_util.utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert len(calls) == 1
    await opp.async_block_till_done()
    assert (
        calls[0].data["some"] == f"turn_off device - {entity_id} - off - on - 0:00:05"
    )
