"""The tests for Arcam FMJ Receiver control device triggers."""
import pytest

from openpeerpower.components.arcam_fmj.const import DOMAIN
import openpeerpower.components.automation as automation
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
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
    """Test we get the expected triggers from a arcam_fmj."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "host", 1234)},
    )
    entity_reg.async_get_or_create(
        "media_player", DOMAIN, "5678", device_id=device_entry.id
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": "media_player.arcam_fmj_5678",
        },
    ]
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)

    # Test triggers are either arcam_fmj specific or media_player entity triggers
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    for expected_trigger in expected_triggers:
        assert expected_trigger in triggers
    for trigger in triggers:
        assert trigger in expected_triggers or trigger["domain"] == "media_player"


async def test_if_fires_on_turn_on_request(opp, calls, player_setup, state):
    """Test for turn_on and turn_off triggers firing."""
    state.get_power.return_value = None

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
                        "entity_id": player_setup,
                        "type": "turn_on",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.entity_id }}",
                            "id": "{{ trigger.id }}",
                        },
                    },
                }
            ]
        },
    )

    await opp.services.async_call(
        "media_player",
        "turn_on",
        {"entity_id": player_setup},
        blocking=True,
    )

    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == player_setup
    assert calls[0].data["id"] == 0
