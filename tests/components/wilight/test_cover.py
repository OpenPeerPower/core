"""Tests for the WiLight integration."""
from unittest.mock import patch

import pytest
import pywilight

from openpeerpower.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import (
    HOST,
    UPNP_MAC_ADDRESS,
    UPNP_MODEL_NAME_COVER,
    UPNP_MODEL_NUMBER,
    UPNP_SERIAL,
    WILIGHT_ID,
    setup_integration,
)


@pytest.fixture(name="dummy_device_from_host_cover")
def mock_dummy_device_from_host_light_fan():
    """Mock a valid api_devce."""

    device = pywilight.wilight_from_discovery(
        f"http://{HOST}:45995/wilight.xml",
        UPNP_MAC_ADDRESS,
        UPNP_MODEL_NAME_COVER,
        UPNP_SERIAL,
        UPNP_MODEL_NUMBER,
    )

    device.set_dummy(True)

    with patch(
        "pywilight.device_from_host",
        return_value=device,
    ):
        yield device


async def test_loading_cover(
    opp: OpenPeerPowerType,
    dummy_device_from_host_cover,
) -> None:
    """Test the WiLight configuration entry loading."""

    entry = await setup_integration.opp)
    assert entry
    assert entry.unique_id == WILIGHT_ID

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    # First segment of the strip
    state = opp.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == STATE_CLOSED

    entry = entity_registry.async_get("cover.wl000000000099_1")
    assert entry
    assert entry.unique_id == "WL000000000099_0"


async def test_open_close_cover_state(
    opp: OpenPeerPowerType, dummy_device_from_host_cover
) -> None:
    """Test the change of state of the cover."""
    await setup_integration.opp)

    # Open
    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await opp.async_block_till_done()
    state = opp.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == STATE_OPENING

    # Close
    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await opp.async_block_till_done()
    state = opp.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == STATE_CLOSING

    # Set position
    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_POSITION: 50, ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await opp.async_block_till_done()
    state = opp.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == STATE_OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 50

    # Stop
    await opp.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: "cover.wl000000000099_1"},
        blocking=True,
    )

    await opp.async_block_till_done()
    state = opp.states.get("cover.wl000000000099_1")
    assert state
    assert state.state == STATE_OPEN
