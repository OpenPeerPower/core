"""Test cases that are in common among wemo platform modules.

This is not a test module. These test methods are used by the platform test modules.
"""
import asyncio
import threading
from unittest.mock import patch

import async_timeout
from pywemo.ouimeaux_device.api.service import ActionException

from openpeerpower.components.openpeerpowerr import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_UNAVAILABLE
from openpeerpowerr.core import callback
from openpeerpowerr.setup import async_setup_component


def _perform_registry_callback.opp, pywemo_registry, pywemo_device):
    """Return a callable method to trigger a state callback from the device."""

    @callback
    def async_callback():
        # Cause a state update callback to be triggered by the device.
        pywemo_registry.callbacks[pywemo_device.name](pywemo_device, "", "")
        return.opp.async_block_till_done()

    return async_callback


def _perform_async_update.opp, wemo_entity):
    """Return a callable method to cause opp to update the state of the entity."""

    @callback
    def async_callback():
        return.opp.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
            blocking=True,
        )

    return async_callback


async def _async_multiple_call_helper(
   .opp,
    pywemo_registry,
    wemo_entity,
    pywemo_device,
    call1,
    call2,
    update_polling_method=None,
):
    """Create two calls (call1 & call2) in parallel; verify only one polls the device.

    The platform entity should only perform one update poll on the device at a time.
    Any parallel updates that happen at the same time should be ignored. This is
    verified by blocking in the update polling method. The polling method should
    only be called once as a result of calling call1 & call2 simultaneously.
    """
    # get_state is called outside the event loop. Use non-async Python Event.
    event = threading.Event()

    def get_update(force_update=True):
        event.wait()

    update_polling_method = update_polling_method or pywemo_device.get_state
    update_polling_method.side_effect = get_update

    # One of these two calls will block on `event`. The other will return right
    # away because the `_update_lock` is held.
    _, pending = await asyncio.wait(
        [call1(), call2()], return_when=asyncio.FIRST_COMPLETED
    )

    # Allow the blocked call to return.
    event.set()
    if pending:
        await asyncio.wait(pending)

    # Make sure the state update only happened once.
    update_polling_method.assert_called_once()


async def test_async_update_locked_callback_and_update(
   .opp, pywemo_registry, wemo_entity, pywemo_device, **kwargs
):
    """Test that a callback and a state update request can't both happen at the same time.

    When a state update is received via a callback from the device at the same time
    as opp is calling `async_update`, verify that only one of the updates proceeds.
    """
    await async_setup_component.opp, HA_DOMAIN, {})
    callback = _perform_registry_callback.opp, pywemo_registry, pywemo_device)
    update = _perform_async_update.opp, wemo_entity)
    await _async_multiple_call_helper(
       .opp, pywemo_registry, wemo_entity, pywemo_device, callback, update, **kwargs
    )


async def test_async_update_locked_multiple_updates(
   .opp, pywemo_registry, wemo_entity, pywemo_device, **kwargs
):
    """Test that two opp async_update state updates do not proceed at the same time."""
    await async_setup_component.opp, HA_DOMAIN, {})
    update = _perform_async_update.opp, wemo_entity)
    await _async_multiple_call_helper(
       .opp, pywemo_registry, wemo_entity, pywemo_device, update, update, **kwargs
    )


async def test_async_update_locked_multiple_callbacks(
   .opp, pywemo_registry, wemo_entity, pywemo_device, **kwargs
):
    """Test that two device callback state updates do not proceed at the same time."""
    await async_setup_component.opp, HA_DOMAIN, {})
    callback = _perform_registry_callback.opp, pywemo_registry, pywemo_device)
    await _async_multiple_call_helper(
       .opp, pywemo_registry, wemo_entity, pywemo_device, callback, callback, **kwargs
    )


async def test_async_locked_update_with_exception(
   .opp, wemo_entity, pywemo_device, update_polling_method=None
):
    """Test that the entity becomes unavailable when communication is lost."""
    assert.opp.states.get(wemo_entity.entity_id).state == STATE_OFF
    await async_setup_component.opp, HA_DOMAIN, {})
    update_polling_method = update_polling_method or pywemo_device.get_state
    update_polling_method.side_effect = ActionException

    await.opp.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
        blocking=True,
    )

    assert.opp.states.get(wemo_entity.entity_id).state == STATE_UNAVAILABLE


async def test_async_update_with_timeout_and_recovery.opp, wemo_entity, pywemo_device):
    """Test that the entity becomes unavailable after a timeout, and that it recovers."""
    assert.opp.states.get(wemo_entity.entity_id).state == STATE_OFF
    await async_setup_component.opp, HA_DOMAIN, {})

    event = threading.Event()

    def get_state(*args):
        event.wait()
        return 0

    if hasattr(pywemo_device, "bridge_update"):
        pywemo_device.bridge_update.side_effect = get_state
    else:
        pywemo_device.get_state.side_effect = get_state
    timeout = async_timeout.timeout(0)

    with patch("async_timeout.timeout", return_value=timeout):
        await.opp.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
            blocking=True,
        )

    assert.opp.states.get(wemo_entity.entity_id).state == STATE_UNAVAILABLE

    # Check that the entity recovers and is available after the update succeeds.
    event.set()
    await opp.async_block_till_done()
    assert.opp.states.get(wemo_entity.entity_id).state == STATE_OFF
