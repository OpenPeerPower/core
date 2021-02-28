"""Tests for the Wemo switch entity."""

import pytest

from openpeerpower.components.openpeerpower import (
    DOMAIN as OP_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component

from . import entity_test_helpers


@pytest.fixture
def pywemo_model():
    """Pywemo LightSwitch models use the switch platform."""
    return "LightSwitch"


# Tests that are in common among wemo platforms. These test methods will be run
# in the scope of this test module. They will run using the pywemo_model from
# this test module (LightSwitch).
test_async_update_locked_multiple_updates = (
    entity_test_helpers.test_async_update_locked_multiple_updates
)
test_async_update_locked_multiple_callbacks = (
    entity_test_helpers.test_async_update_locked_multiple_callbacks
)
test_async_update_locked_callback_and_update = (
    entity_test_helpers.test_async_update_locked_callback_and_update
)
test_async_locked_update_with_exception = (
    entity_test_helpers.test_async_locked_update_with_exception
)
test_async_update_with_timeout_and_recovery = (
    entity_test_helpers.test_async_update_with_timeout_and_recovery
)


async def test_switch_registry_state_callback(
    opp, pywemo_registry, pywemo_device, wemo_entity
):
    """Verify that the switch receives state updates from the registry."""
    # On state.
    pywemo_device.get_state.return_value = 1
    pywemo_registry.callbacks[pywemo_device.name](pywemo_device, "", "")
    await opp.async_block_till_done()
    assert opp.states.get(wemo_entity.entity_id).state == STATE_ON

    # Off state.
    pywemo_device.get_state.return_value = 0
    pywemo_registry.callbacks[pywemo_device.name](pywemo_device, "", "")
    await opp.async_block_till_done()
    assert opp.states.get(wemo_entity.entity_id).state == STATE_OFF


async def test_switch_update_entity(opp, pywemo_registry, pywemo_device, wemo_entity):
    """Verify that the switch performs state updates."""
    await async_setup_component(opp, OP_DOMAIN, {})

    # On state.
    pywemo_device.get_state.return_value = 1
    await opp.services.async_call(
        OP_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
        blocking=True,
    )
    assert opp.states.get(wemo_entity.entity_id).state == STATE_ON

    # Off state.
    pywemo_device.get_state.return_value = 0
    await opp.services.async_call(
        OP_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
        blocking=True,
    )
    assert opp.states.get(wemo_entity.entity_id).state == STATE_OFF
