"""Tests for the Wemo light entity via the bridge."""
from unittest.mock import create_autospec, patch

import pytest
import pywemo

from openpeerpower.components.openpeerpower import (
    DOMAIN as OP_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from openpeerpower.components.wemo.light import MIN_TIME_BETWEEN_SCANS
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from . import entity_test_helpers


@pytest.fixture
def pywemo_model():
    """Pywemo Bridge models use the light platform (WemoLight class)."""
    return "Bridge"


# Note: The ordering of where the pywemo_bridge_light comes in test arguments matters.
# In test methods, the pywemo_bridge_light fixture argument must come before the
# wemo_entity fixture argument.
@pytest.fixture(name="pywemo_bridge_light")
def pywemo_bridge_light_fixture(pywemo_device):
    """Fixture for Bridge.Light WeMoDevice instances."""
    light = create_autospec(pywemo.ouimeaux_device.bridge.Light, instance=True)
    light.uniqueID = pywemo_device.serialnumber
    light.name = pywemo_device.name
    light.bridge = pywemo_device
    light.state = {"onoff": 0}
    pywemo_device.Lights = {pywemo_device.serialnumber: light}
    return light


def _bypass_throttling():
    """Bypass the util.Throttle on the update_lights method."""
    utcnow = dt_util.utcnow()

    def increment_and_return_time():
        nonlocal utcnow
        utcnow += MIN_TIME_BETWEEN_SCANS
        return utcnow

    return patch("openpeerpower.util.utcnow", side_effect=increment_and_return_time)


async def test_async_update_locked_multiple_updates(
    opp. pywemo_registry, pywemo_bridge_light, wemo_entity, pywemo_device
):
    """Test that two state updates do not proceed at the same time."""
    pywemo_device.bridge_update.reset_mock()

    with _bypass_throttling():
        await entity_test_helpers.test_async_update_locked_multiple_updates(
            opp.
            pywemo_registry,
            wemo_entity,
            pywemo_device,
            update_polling_method=pywemo_device.bridge_update,
        )


async def test_async_update_with_timeout_and_recovery(
    opp. pywemo_bridge_light, wemo_entity, pywemo_device
):
    """Test that the entity becomes unavailable after a timeout, and that it recovers."""
    with _bypass_throttling():
        await entity_test_helpers.test_async_update_with_timeout_and_recovery(
            opp. wemo_entity, pywemo_device
        )


async def test_async_locked_update_with_exception(
    opp. pywemo_bridge_light, wemo_entity, pywemo_device
):
    """Test that the entity becomes unavailable when communication is lost."""
    with _bypass_throttling():
        await entity_test_helpers.test_async_locked_update_with_exception(
            opp.
            wemo_entity,
            pywemo_device,
            update_polling_method=pywemo_device.bridge_update,
        )


async def test_light_update_entity(
    opp. pywemo_registry, pywemo_bridge_light, wemo_entity
):
    """Verify that the light performs state updates."""
    await async_setup_component.opp, OP_DOMAIN, {})

    # On state.
    pywemo_bridge_light.state = {"onoff": 1}
    await opp.services.async_call(
        OP_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
        blocking=True,
    )
    assert.opp.states.get(wemo_entity.entity_id).state == STATE_ON

    # Off state.
    pywemo_bridge_light.state = {"onoff": 0}
    await opp.services.async_call(
        OP_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
        blocking=True,
    )
    assert.opp.states.get(wemo_entity.entity_id).state == STATE_OFF
