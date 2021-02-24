"""Test Bluetooth LE device tracker."""

from datetime import timedelta
from unittest.mock import patch

from openpeerpower.components.bluetooth_le_tracker import device_tracker
from openpeerpower.components.device_tracker.const import (
    CONF_SCAN_INTERVAL,
    CONF_TRACK_NEW,
    DOMAIN,
)
from openpeerpower.const import CONF_PLATFORM
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt as dt_util, slugify

from tests.common import async_fire_time_changed


async def test_preserve_new_tracked_device_name.opp, mock_device_tracker_conf):
    """Test preserving tracked device name across new seens."""

    address = "DE:AD:BE:EF:13:37"
    name = "Mock device name"
    entity_id = f"{DOMAIN}.{slugify(name)}"

    with patch(
        "openpeerpower.components."
        "bluetooth_le_tracker.device_tracker.pygatt.GATTToolBackend"
    ) as mock_backend, patch.object(device_tracker, "MIN_SEEN_NEW", 3):

        # Return with name when seen first time
        device = {"address": address, "name": name}
        mock_backend.return_value.scan.return_value = [device]

        config = {
            CONF_PLATFORM: "bluetooth_le_tracker",
            CONF_SCAN_INTERVAL: timedelta(minutes=1),
            CONF_TRACK_NEW: True,
        }
        result = await async_setup_component.opp, DOMAIN, {DOMAIN: config})
        assert result

        # Seen once here; return without name when seen subsequent times
        device["name"] = None

        # Tick until device seen enough times for to be registered for tracking
        for _ in range(device_tracker.MIN_SEEN_NEW - 1):
            async_fire_time_changed(
                opp,
                dt_util.utcnow() + config[CONF_SCAN_INTERVAL] + timedelta(seconds=1),
            )
            await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state
    assert state.name == name
