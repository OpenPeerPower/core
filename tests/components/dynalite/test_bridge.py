"""Test Dynalite bridge."""


from unittest.mock import AsyncMock, Mock, patch

from dynalite_devices_lib.dynalite_devices import (
    CONF_AREA as dyn_CONF_AREA,
    CONF_PRESET as dyn_CONF_PRESET,
    NOTIFICATION_PACKET,
    NOTIFICATION_PRESET,
    DynaliteNotification,
)

from openpeerpower.components import dynalite
from openpeerpower.components.dynalite.const import (
    ATTR_AREA,
    ATTR_HOST,
    ATTR_PACKET,
    ATTR_PRESET,
)
from openpeerpowerr.helpers.dispatcher import async_dispatcher_connect

from tests.common import MockConfigEntry


async def test_update_device.opp):
    """Test that update works."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={dynalite.CONF_HOST: host})
    entry.add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await.opp.config_entries.async_setup(entry.entry_id)
        # Not waiting so it add the devices before registration
        update_device_func = mock_dyn_dev.mock_calls[1][2]["update_device_func"]
    device = Mock()
    device.unique_id = "abcdef"
    wide_func = Mock()
    async_dispatcher_connect.opp, f"dynalite-update-{host}", wide_func)
    specific_func = Mock()
    async_dispatcher_connect(
       .opp, f"dynalite-update-{host}-{device.unique_id}", specific_func
    )
    update_device_func()
    await opp.async_block_till_done()
    wide_func.assert_called_once()
    specific_func.assert_not_called()
    update_device_func(device)
    await opp.async_block_till_done()
    wide_func.assert_called_once()
    specific_func.assert_called_once()


async def test_add_devices_then_register.opp):
    """Test that add_devices work."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={dynalite.CONF_HOST: host})
    entry.add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await.opp.config_entries.async_setup(entry.entry_id)
        # Not waiting so it add the devices before registration
        new_device_func = mock_dyn_dev.mock_calls[1][2]["new_device_func"]
    # Now with devices
    device1 = Mock()
    device1.category = "light"
    device1.name = "NAME"
    device1.unique_id = "unique1"
    device2 = Mock()
    device2.category = "switch"
    device2.name = "NAME2"
    device2.unique_id = "unique2"
    new_device_func([device1, device2])
    device3 = Mock()
    device3.category = "switch"
    device3.name = "NAME3"
    device3.unique_id = "unique3"
    new_device_func([device3])
    await opp.async_block_till_done()
    assert.opp.states.get("light.name")
    assert.opp.states.get("switch.name2")
    assert.opp.states.get("switch.name3")


async def test_register_then_add_devices.opp):
    """Test that add_devices work after register_add_entities."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={dynalite.CONF_HOST: host})
    entry.add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await.opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        new_device_func = mock_dyn_dev.mock_calls[1][2]["new_device_func"]
    # Now with devices
    device1 = Mock()
    device1.category = "light"
    device1.name = "NAME"
    device1.unique_id = "unique1"
    device2 = Mock()
    device2.category = "switch"
    device2.name = "NAME2"
    device2.unique_id = "unique2"
    new_device_func([device1, device2])
    await opp.async_block_till_done()
    assert.opp.states.get("light.name")
    assert.opp.states.get("switch.name2")


async def test_notifications.opp):
    """Test that update works."""
    host = "1.2.3.4"
    entry = MockConfigEntry(domain=dynalite.DOMAIN, data={dynalite.CONF_HOST: host})
    entry.add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await.opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        notification_func = mock_dyn_dev.mock_calls[1][2]["notification_func"]
    event_listener1 = Mock()
   .opp.bus.async_listen("dynalite_packet", event_listener1)
    packet = [5, 4, 3, 2]
    notification_func(
        DynaliteNotification(NOTIFICATION_PACKET, {NOTIFICATION_PACKET: packet})
    )
    await opp.async_block_till_done()
    event_listener1.assert_called_once()
    my_event = event_listener1.mock_calls[0][1][0]
    assert my_event.data[ATTR_HOST] == host
    assert my_event.data[ATTR_PACKET] == packet
    event_listener2 = Mock()
   .opp.bus.async_listen("dynalite_preset", event_listener2)
    notification_func(
        DynaliteNotification(
            NOTIFICATION_PRESET, {dyn_CONF_AREA: 7, dyn_CONF_PRESET: 2}
        )
    )
    await opp.async_block_till_done()
    event_listener2.assert_called_once()
    my_event = event_listener2.mock_calls[0][1][0]
    assert my_event.data[ATTR_HOST] == host
    assert my_event.data[ATTR_AREA] == 7
    assert my_event.data[ATTR_PRESET] == 2
