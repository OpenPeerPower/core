"""The tests for Philips TV device triggers."""
import pytest

import openpeerpower.components.automation as automation
from openpeerpower.components.philips_js.const import DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import (
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
)
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_triggers(opp, mock_device):
    """Test we get the expected triggers."""
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "turn_on",
            "device_id": mock_device.id,
        },
    ]
    triggers = await async_get_device_automations(opp, "trigger", mock_device.id)
    assert_lists_same(triggers, expected_triggers)


async def test_if_fires_on_turn_on_request(opp, calls, mock_entity, mock_device):
    """Test for turn_on and turn_off triggers firing."""

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": mock_device.id,
                        "type": "turn_on",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "{{ trigger.device_id }}"},
                    },
                }
            ]
        },
    )

    await opp.services.async_call(
        "media_player",
        "turn_on",
        {"entity_id": mock_entity},
        blocking=True,
    )

    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == mock_device.id
