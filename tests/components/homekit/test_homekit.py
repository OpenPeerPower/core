"""Tests for the HomeKit component."""
import os
from typing import Dict
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_CAMERA, CATEGORY_TELEVISION
import pytest

from openpeerpower import config as.opp_config
from openpeerpower.components import zeroconf
from openpeerpower.components.binary_sensor import (
    DEVICE_CLASS_BATTERY_CHARGING,
    DEVICE_CLASS_MOTION,
)
from openpeerpower.components.homekit import (
    MAX_DEVICES,
    STATUS_READY,
    STATUS_RUNNING,
    STATUS_STOPPED,
    STATUS_WAIT,
    HomeKit,
)
from openpeerpower.components.homekit.accessories import HomeBridge
from openpeerpower.components.homekit.const import (
    AID_STORAGE,
    BRIDGE_NAME,
    BRIDGE_SERIAL_NUMBER,
    CONF_AUTO_START,
    DEFAULT_PORT,
    DOMAIN,
    HOMEKIT,
    HOMEKIT_MODE_ACCESSORY,
    HOMEKIT_MODE_BRIDGE,
    SERVICE_HOMEKIT_RESET_ACCESSORY,
    SERVICE_HOMEKIT_START,
)
from openpeerpower.components.homekit.util import get_persist_fullpath_for_entry_id
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PORT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    EVENT_OPENPEERPOWER_STARTED,
    EVENT_OPENPEERPOWER_STOP,
    PERCENTAGE,
    SERVICE_RELOAD,
    STATE_ON,
)
from openpeerpower.core import State
from openpeerpower.helpers import device_registry
from openpeerpower.helpers.entityfilter import generate_filter
from openpeerpower.setup import async_setup_component
from openpeerpower.util import json as json_util

from .util import PATH_HOMEKIT, async_init_entry, async_init_integration

from tests.common import MockConfigEntry, mock_device_registry, mock_registry

IP_ADDRESS = "127.0.0.1"


@pytest.fixture(autouse=True)
def always_patch_driver(hk_driver):
    """Load the hk_driver fixture."""


@pytest.fixture(name="device_reg")
def device_reg_fixture.opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry.opp)


@pytest.fixture(name="entity_reg")
def entity_reg_fixture.opp):
    """Return an empty, loaded, registry."""
    return mock_registry.opp)


async def test_setup_min.opp, mock_zeroconf):
    """Test async_setup with min config options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: BRIDGE_NAME, CONF_PORT: DEFAULT_PORT},
        options={},
    )
    entry.add_to.opp.opp)

    with patch(f"{PATH_HOMEKIT}.HomeKit") as mock_homekit:
        mock_homekit.return_value = homekit = Mock()
        type(homekit).async_start = AsyncMock()
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    mock_homekit.assert_any_call(
        opp,
        BRIDGE_NAME,
        DEFAULT_PORT,
        None,
        ANY,
        {},
        HOMEKIT_MODE_BRIDGE,
        None,
        entry.entry_id,
    )
    assert mock_homekit().setup.called is True

    # Test auto start enabled
    mock_homekit.reset_mock()
   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
    await opp.async_block_till_done()

    mock_homekit().async_start.assert_called()


async def test_setup_auto_start_disabled.opp, mock_zeroconf):
    """Test async_setup with auto start disabled and test service calls."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "Test Name", CONF_PORT: 11111, CONF_IP_ADDRESS: "172.0.0.0"},
        options={CONF_AUTO_START: False},
    )
    entry.add_to.opp.opp)

    with patch(f"{PATH_HOMEKIT}.HomeKit") as mock_homekit:
        mock_homekit.return_value = homekit = Mock()
        type(homekit).async_start = AsyncMock()
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    mock_homekit.assert_any_call(
        opp,
        "Test Name",
        11111,
        "172.0.0.0",
        ANY,
        {},
        HOMEKIT_MODE_BRIDGE,
        None,
        entry.entry_id,
    )
    assert mock_homekit().setup.called is True

    # Test auto_start disabled
    homekit.reset_mock()
    homekit.async_start.reset_mock()
   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
    await opp.async_block_till_done()
    assert homekit.async_start.called is False

    # Test start call with driver is ready
    homekit.reset_mock()
    homekit.async_start.reset_mock()
    homekit.status = STATUS_READY

    await opp.services.async_call(DOMAIN, SERVICE_HOMEKIT_START, blocking=True)
    await opp.async_block_till_done()
    assert homekit.async_start.called is True

    # Test start call with driver started
    homekit.reset_mock()
    homekit.async_start.reset_mock()
    homekit.status = STATUS_STOPPED

    await opp.services.async_call(DOMAIN, SERVICE_HOMEKIT_START, blocking=True)
    await opp.async_block_till_done()
    assert homekit.async_start.called is False


async def test_homekit_setup_opp, hk_driver, mock_zeroconf):
    """Test setup of bridge and driver."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        source=SOURCE_IMPORT,
    )
    homekit = HomeKit(
        opp,
        BRIDGE_NAME,
        DEFAULT_PORT,
        None,
        {},
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )

   .opp.states.async_set("light.demo", "on")
   .opp.states.async_set("light.demo2", "on")
    zeroconf_mock = MagicMock()
    with patch(
        f"{PATH_HOMEKIT}.HomeDriver", return_value=hk_driver
    ) as mock_driver, patch("openpeerpower.util.get_local_ip") as mock_ip:
        mock_ip.return_value = IP_ADDRESS
        await opp.async_add_executor_job(homekit.setup, zeroconf_mock)

    path = get_persist_fullpath_for_entry_id.opp, entry.entry_id)
    mock_driver.assert_called_with(
        opp,
        entry.entry_id,
        BRIDGE_NAME,
        loop.opp.loop,
        address=IP_ADDRESS,
        port=DEFAULT_PORT,
        persist_file=path,
        advertised_address=None,
        zeroconf_instance=zeroconf_mock,
    )
    assert homekit.driver.safe_mode is False

    # Test if stop listener is setup
    assert.opp.bus.async_listeners().get(EVENT_OPENPEERPOWER_STOP) == 1


async def test_homekit_setup_ip_address.opp, hk_driver, mock_zeroconf):
    """Test setup with given IP address."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        source=SOURCE_IMPORT,
    )
    homekit = HomeKit(
        opp,
        BRIDGE_NAME,
        DEFAULT_PORT,
        "172.0.0.0",
        {},
        {},
        HOMEKIT_MODE_BRIDGE,
        None,
        entry_id=entry.entry_id,
    )

    mock_zeroconf = MagicMock()
    path = get_persist_fullpath_for_entry_id.opp, entry.entry_id)
    with patch(f"{PATH_HOMEKIT}.HomeDriver", return_value=hk_driver) as mock_driver:
        await opp.async_add_executor_job(homekit.setup, mock_zeroconf)
    mock_driver.assert_called_with(
        opp,
        entry.entry_id,
        BRIDGE_NAME,
        loop.opp.loop,
        address="172.0.0.0",
        port=DEFAULT_PORT,
        persist_file=path,
        advertised_address=None,
        zeroconf_instance=mock_zeroconf,
    )


async def test_homekit_setup_advertise_ip.opp, hk_driver, mock_zeroconf):
    """Test setup with given IP address to advertise."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        source=SOURCE_IMPORT,
    )
    homekit = HomeKit(
        opp,
        BRIDGE_NAME,
        DEFAULT_PORT,
        "0.0.0.0",
        {},
        {},
        HOMEKIT_MODE_BRIDGE,
        "192.168.1.100",
        entry_id=entry.entry_id,
    )

    zeroconf_instance = MagicMock()
    path = get_persist_fullpath_for_entry_id.opp, entry.entry_id)
    with patch(f"{PATH_HOMEKIT}.HomeDriver", return_value=hk_driver) as mock_driver:
        await opp.async_add_executor_job(homekit.setup, zeroconf_instance)
    mock_driver.assert_called_with(
        opp,
        entry.entry_id,
        BRIDGE_NAME,
        loop.opp.loop,
        address="0.0.0.0",
        port=DEFAULT_PORT,
        persist_file=path,
        advertised_address="192.168.1.100",
        zeroconf_instance=zeroconf_instance,
    )


async def test_homekit_add_accessory.opp, mock_zeroconf):
    """Add accessory if config exists and get_acc returns an accessory."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        lambda entity_id: True,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = "driver"
    homekit.bridge = mock_bridge = Mock()
    homekit.bridge.accessories = range(10)

    mock_acc = Mock(category="any")

    await async_init_integration.opp)

    with patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc:
        mock_get_acc.side_effect = [None, mock_acc, None]
        homekit.add_bridge_accessory(State("light.demo", "on"))
        mock_get_acc.assert_called_with.opp, "driver", ANY, 1403373688, {})
        assert not mock_bridge.add_accessory.called

        homekit.add_bridge_accessory(State("demo.test", "on"))
        mock_get_acc.assert_called_with.opp, "driver", ANY, 600325356, {})
        assert mock_bridge.add_accessory.called

        homekit.add_bridge_accessory(State("demo.test_2", "on"))
        mock_get_acc.assert_called_with.opp, "driver", ANY, 1467253281, {})
        mock_bridge.add_accessory.assert_called_with(mock_acc)


@pytest.mark.parametrize("acc_category", [CATEGORY_TELEVISION, CATEGORY_CAMERA])
async def test_homekit_warn_add_accessory_bridge(
    opp, acc_category, mock_zeroconf, caplog
):
    """Test we warn when adding cameras or tvs to a bridge."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        lambda entity_id: True,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = "driver"
    homekit.bridge = mock_bridge = Mock()
    homekit.bridge.accessories = range(10)

    mock_camera_acc = Mock(category=acc_category)

    await async_init_integration.opp)

    with patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc:
        mock_get_acc.side_effect = [None, mock_camera_acc, None]
        homekit.add_bridge_accessory(State("light.demo", "on"))
        mock_get_acc.assert_called_with.opp, "driver", ANY, 1403373688, {})
        assert not mock_bridge.add_accessory.called

        homekit.add_bridge_accessory(State("camera.test", "on"))
        mock_get_acc.assert_called_with.opp, "driver", ANY, 1508819236, {})
        assert mock_bridge.add_accessory.called

    assert "accessory mode" in caplog.text


async def test_homekit_remove_accessory.opp, mock_zeroconf):
    """Remove accessory from bridge."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        lambda entity_id: True,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = "driver"
    homekit.bridge = mock_bridge = Mock()
    mock_bridge.accessories = {"light.demo": "acc"}

    acc = homekit.remove_bridge_accessory("light.demo")
    assert acc == "acc"
    assert len(mock_bridge.accessories) == 0


async def test_homekit_entity_filter.opp, mock_zeroconf):
    """Test the entity filter."""
    entry = await async_init_integration.opp)

    entity_filter = generate_filter(["cover"], ["demo.test"], [], [])
    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        entity_filter,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.bridge = Mock()
    homekit.bridge.accessories = {}

    with patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc:
        mock_get_acc.return_value = None

        homekit.add_bridge_accessory(State("cover.test", "open"))
        assert mock_get_acc.called is True
        mock_get_acc.reset_mock()

        homekit.add_bridge_accessory(State("demo.test", "on"))
        assert mock_get_acc.called is True
        mock_get_acc.reset_mock()

        homekit.add_bridge_accessory(State("light.demo", "light"))
        assert mock_get_acc.called is False


async def test_homekit_entity_glob_filter.opp, mock_zeroconf):
    """Test the entity filter."""
    entry = await async_init_integration.opp)

    entity_filter = generate_filter(
        ["cover"], ["demo.test"], [], [], ["*.included_*"], ["*.excluded_*"]
    )
    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        entity_filter,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.bridge = Mock()
    homekit.bridge.accessories = {}

    with patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc:
        mock_get_acc.return_value = None

        homekit.add_bridge_accessory(State("cover.test", "open"))
        assert mock_get_acc.called is True
        mock_get_acc.reset_mock()

        homekit.add_bridge_accessory(State("demo.test", "on"))
        assert mock_get_acc.called is True
        mock_get_acc.reset_mock()

        homekit.add_bridge_accessory(State("cover.excluded_test", "open"))
        assert mock_get_acc.called is False
        mock_get_acc.reset_mock()

        homekit.add_bridge_accessory(State("light.included_test", "light"))
        assert mock_get_acc.called is True
        mock_get_acc.reset_mock()


async def test_homekit_start.opp, hk_driver, device_reg):
    """Test HomeKit start method."""
    entry = await async_init_integration.opp)

    pin = b"123-45-678"
    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.bridge = Mock()
    homekit.bridge.accessories = []
    homekit.driver = hk_driver
    # pylint: disable=protected-access
    homekit._filter = Mock(return_value=True)
    homekit.driver.accessory = Accessory(hk_driver, "any")

    connection = (device_registry.CONNECTION_NETWORK_MAC, "AA:BB:CC:DD:EE:FF")
    bridge_with_wrong_mac = device_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={connection},
        manufacturer="Any",
        name="Any",
        model="Open Peer Power HomeKit Bridge",
    )

   .opp.states.async_set("light.demo", "on")
   .opp.states.async_set("light.demo2", "on")
    state = opp.states.async_all()[0]

    with patch(f"{PATH_HOMEKIT}.HomeKit.add_bridge_accessory") as mock_add_acc, patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ) as mock_setup_msg, patch(
        "pyhap.accessory_driver.AccessoryDriver.add_accessory"
    ) as hk_driver_add_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ) as hk_driver_start:
        await homekit.async_start()

    await opp.async_block_till_done()
    mock_add_acc.assert_any_call(state)
    mock_setup_msg.assert_called_with.opp, entry.entry_id, None, pin, ANY)
    hk_driver_add_acc.assert_called_with(homekit.bridge)
    assert hk_driver_start.called
    assert homekit.status == STATUS_RUNNING

    # Test start() if already started
    hk_driver_start.reset_mock()
    await homekit.async_start()
    await opp.async_block_till_done()
    assert not hk_driver_start.called

    assert device_reg.async_get(bridge_with_wrong_mac.id) is None

    device = device_reg.async_get_device(
        {(DOMAIN, entry.entry_id, BRIDGE_SERIAL_NUMBER)}
    )
    assert device
    formatted_mac = device_registry.format_mac(homekit.driver.state.mac)
    assert (device_registry.CONNECTION_NETWORK_MAC, formatted_mac) in device.connections

    # Start again to make sure the registry entry is kept
    homekit.status = STATUS_READY
    with patch(f"{PATH_HOMEKIT}.HomeKit.add_bridge_accessory") as mock_add_acc, patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ) as mock_setup_msg, patch(
        "pyhap.accessory_driver.AccessoryDriver.add_accessory"
    ) as hk_driver_add_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ) as hk_driver_start:
        await homekit.async_start()

    device = device_reg.async_get_device(
        {(DOMAIN, entry.entry_id, BRIDGE_SERIAL_NUMBER)}
    )
    assert device
    formatted_mac = device_registry.format_mac(homekit.driver.state.mac)
    assert (device_registry.CONNECTION_NETWORK_MAC, formatted_mac) in device.connections

    assert len(device_reg.devices) == 1


async def test_homekit_start_with_a_broken_accessory.opp, hk_driver, mock_zeroconf):
    """Test HomeKit start method."""
    pin = b"123-45-678"
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_NAME: "mock_name", CONF_PORT: 12345}
    )
    entity_filter = generate_filter(["cover", "light"], ["demo.test"], [], [])

    await async_init_entry.opp, entry)
    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        entity_filter,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )

    homekit.bridge = Mock()
    homekit.bridge.accessories = []
    homekit.driver = hk_driver
    homekit.driver.accessory = Accessory(hk_driver, "any")

   .opp.states.async_set("light.demo", "on")
   .opp.states.async_set("light.broken", "on")

    with patch(f"{PATH_HOMEKIT}.get_accessory", side_effect=Exception), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ) as mock_setup_msg, patch(
        "pyhap.accessory_driver.AccessoryDriver.add_accessory",
    ) as hk_driver_add_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ) as hk_driver_start:
        await homekit.async_start()

    await opp.async_block_till_done()
    mock_setup_msg.assert_called_with.opp, entry.entry_id, None, pin, ANY)
    hk_driver_add_acc.assert_called_with(homekit.bridge)
    assert hk_driver_start.called
    assert homekit.status == STATUS_RUNNING

    # Test start() if already started
    hk_driver_start.reset_mock()
    await homekit.async_start()
    await opp.async_block_till_done()
    assert not hk_driver_start.called


async def test_homekit_stop.opp):
    """Test HomeKit stop method."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = Mock()
    homekit.driver.async_stop = AsyncMock()
    homekit.bridge = Mock()
    homekit.bridge.accessories = {}

    assert homekit.status == STATUS_READY
    await homekit.async_stop()
    await opp.async_block_till_done()
    homekit.status = STATUS_WAIT
    await homekit.async_stop()
    await opp.async_block_till_done()
    homekit.status = STATUS_STOPPED
    await homekit.async_stop()
    await opp.async_block_till_done()
    assert homekit.driver.async_stop.called is False

    # Test if driver is started
    homekit.status = STATUS_RUNNING
    await homekit.async_stop()
    await opp.async_block_till_done()
    assert homekit.driver.async_stop.called is True


async def test_homekit_reset_accessories.opp, mock_zeroconf):
    """Test adding too many accessories to HomeKit."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_NAME: "mock_name", CONF_PORT: 12345}
    )
    entity_id = "light.demo"
    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {entity_id: {}},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.bridge = Mock()
    homekit.bridge.accessories = {}

    with patch(f"{PATH_HOMEKIT}.HomeKit", return_value=homekit), patch(
        f"{PATH_HOMEKIT}.HomeKit.setup"
    ), patch("pyhap.accessory.Bridge.add_accessory") as mock_add_accessory, patch(
        "pyhap.accessory_driver.AccessoryDriver.config_changed"
    ) as hk_driver_config_changed, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        await async_init_entry.opp, entry)

        aid = opp.data[DOMAIN][entry.entry_id][
            AID_STORAGE
        ].get_or_allocate_aid_for_entity_id(entity_id)
        homekit.bridge.accessories = {aid: "acc"}
        homekit.status = STATUS_RUNNING

        await opp.services.async_call(
            DOMAIN,
            SERVICE_HOMEKIT_RESET_ACCESSORY,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await opp.async_block_till_done()

        assert hk_driver_config_changed.call_count == 2
        assert mock_add_accessory.called
        homekit.status = STATUS_READY


async def test_homekit_too_many_accessories.opp, hk_driver, caplog, mock_zeroconf):
    """Test adding too many accessories to HomeKit."""
    entry = await async_init_integration.opp)

    entity_filter = generate_filter(["cover", "light"], ["demo.test"], [], [])

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        entity_filter,
        {},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )

    def _mock_bridge(*_):
        mock_bridge = HomeBridge.opp, hk_driver, "mock_bridge")
        # The bridge itself counts as an accessory
        mock_bridge.accessories = range(MAX_DEVICES)
        return mock_bridge

    homekit.driver = hk_driver
    homekit.driver.accessory = Accessory(hk_driver, "any")

   .opp.states.async_set("light.demo", "on")
   .opp.states.async_set("light.demo2", "on")
   .opp.states.async_set("light.demo3", "on")

    with patch("pyhap.accessory_driver.AccessoryDriver.start_service"), patch(
        "pyhap.accessory_driver.AccessoryDriver.add_accessory"
    ), patch(f"{PATH_HOMEKIT}.show_setup_message"), patch(
        f"{PATH_HOMEKIT}.HomeBridge", _mock_bridge
    ):
        await homekit.async_start()
        await opp.async_block_till_done()
        assert "would exceed" in caplog.text


async def test_homekit_finds_linked_batteries(
    opp, hk_driver, device_reg, entity_reg, mock_zeroconf
):
    """Test HomeKit start method."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {"light.demo": {}},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = hk_driver
    # pylint: disable=protected-access
    homekit._filter = Mock(return_value=True)
    homekit.bridge = HomeBridge.opp, hk_driver, "mock_bridge")

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        sw_version="0.16.0",
        model="Powerwall 2",
        manufacturer="Tesla",
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    binary_charging_sensor = entity_reg.async_get_or_create(
        "binary_sensor",
        "powerwall",
        "battery_charging",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_BATTERY_CHARGING,
    )
    battery_sensor = entity_reg.async_get_or_create(
        "sensor",
        "powerwall",
        "battery",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_BATTERY,
    )
    light = entity_reg.async_get_or_create(
        "light", "powerwall", "demo", device_id=device_entry.id
    )

   .opp.states.async_set(
        binary_charging_sensor.entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY_CHARGING},
    )
   .opp.states.async_set(
        battery_sensor.entity_id, 30, {ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY}
    )
   .opp.states.async_set(light.entity_id, STATE_ON)

    def _mock_get_accessory(*args, **kwargs):
        return [None, "acc", None]

    with patch.object(homekit.bridge, "add_accessory"), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ), patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        await homekit.async_start()
    await opp.async_block_till_done()

    mock_get_acc.assert_called_with(
        opp,
        hk_driver,
        ANY,
        ANY,
        {
            "manufacturer": "Tesla",
            "model": "Powerwall 2",
            "sw_version": "0.16.0",
            "linked_battery_charging_sensor": "binary_sensor.powerwall_battery_charging",
            "linked_battery_sensor": "sensor.powerwall_battery",
        },
    )


async def test_homekit_async_get_integration_fails(
    opp, hk_driver, device_reg, entity_reg, mock_zeroconf
):
    """Test that we continue if async_get_integration fails."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {"light.demo": {}},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = hk_driver
    # pylint: disable=protected-access
    homekit._filter = Mock(return_value=True)
    homekit.bridge = HomeBridge.opp, hk_driver, "mock_bridge")

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        sw_version="0.16.0",
        model="Powerwall 2",
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    binary_charging_sensor = entity_reg.async_get_or_create(
        "binary_sensor",
        "invalid_integration_does_not_exist",
        "battery_charging",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_BATTERY_CHARGING,
    )
    battery_sensor = entity_reg.async_get_or_create(
        "sensor",
        "invalid_integration_does_not_exist",
        "battery",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_BATTERY,
    )
    light = entity_reg.async_get_or_create(
        "light", "invalid_integration_does_not_exist", "demo", device_id=device_entry.id
    )

   .opp.states.async_set(
        binary_charging_sensor.entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY_CHARGING},
    )
   .opp.states.async_set(
        battery_sensor.entity_id, 30, {ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY}
    )
   .opp.states.async_set(light.entity_id, STATE_ON)

    def _mock_get_accessory(*args, **kwargs):
        return [None, "acc", None]

    with patch.object(homekit.bridge, "add_accessory"), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ), patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        await homekit.async_start()
    await opp.async_block_till_done()

    mock_get_acc.assert_called_with(
        opp,
        hk_driver,
        ANY,
        ANY,
        {
            "model": "Powerwall 2",
            "sw_version": "0.16.0",
            "platform": "invalid_integration_does_not_exist",
            "linked_battery_charging_sensor": "binary_sensor.invalid_integration_does_not_exist_battery_charging",
            "linked_battery_sensor": "sensor.invalid_integration_does_not_exist_battery",
        },
    )


async def test_yaml_updates_update_config_entry_for_name.opp, mock_zeroconf):
    """Test async_setup with imported config."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_IMPORT,
        data={CONF_NAME: BRIDGE_NAME, CONF_PORT: DEFAULT_PORT},
        options={},
    )
    entry.add_to.opp.opp)

    with patch(f"{PATH_HOMEKIT}.HomeKit") as mock_homekit:
        mock_homekit.return_value = homekit = Mock()
        type(homekit).async_start = AsyncMock()
        assert await async_setup_component(
            opp, "homekit", {"homekit": {CONF_NAME: BRIDGE_NAME, CONF_PORT: 12345}}
        )
        await opp.async_block_till_done()

    mock_homekit.assert_any_call(
        opp,
        BRIDGE_NAME,
        12345,
        None,
        ANY,
        {},
        HOMEKIT_MODE_BRIDGE,
        None,
        entry.entry_id,
    )
    assert mock_homekit().setup.called is True

    # Test auto start enabled
    mock_homekit.reset_mock()
   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
    await opp.async_block_till_done()

    mock_homekit().async_start.assert_called()


async def test_raise_config_entry_not_ready.opp, mock_zeroconf):
    """Test async_setup when the port is not available."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: BRIDGE_NAME, CONF_PORT: DEFAULT_PORT},
        options={},
    )
    entry.add_to.opp.opp)

    with patch(f"{PATH_HOMEKIT}.HomeKit.setup", side_effect=OSError):
        assert not await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()


async def test_homekit_uses_system_zeroconf.opp, hk_driver, mock_zeroconf):
    """Test HomeKit uses system zeroconf."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: BRIDGE_NAME, CONF_PORT: DEFAULT_PORT},
        options={},
    )
    assert await async_setup_component.opp, "zeroconf", {"zeroconf": {}})
    system_zc = await zeroconf.async_get_instance.opp)

    with patch("pyhap.accessory_driver.AccessoryDriver.start_service"), patch(
        f"{PATH_HOMEKIT}.HomeKit.async_stop"
    ):
        entry.add_to.opp.opp)
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        assert.opp.data[DOMAIN][entry.entry_id][HOMEKIT].driver.advertiser == system_zc
        assert await opp.config_entries.async_unload(entry.entry_id)
        await opp.async_block_till_done()


def _write_data(path: str, data: Dict) -> None:
    """Write the data."""
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    json_util.save_json(path, data)


async def test_homekit_ignored_missing_devices(
    opp, hk_driver, device_reg, entity_reg, mock_zeroconf
):
    """Test HomeKit handles a device in the entity registry but missing from the device registry."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {"light.demo": {}},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = hk_driver
    # pylint: disable=protected-access
    homekit._filter = Mock(return_value=True)
    homekit.bridge = HomeBridge.opp, hk_driver, "mock_bridge")

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        sw_version="0.16.0",
        model="Powerwall 2",
        manufacturer="Tesla",
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    entity_reg.async_get_or_create(
        "binary_sensor",
        "powerwall",
        "battery_charging",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_BATTERY_CHARGING,
    )
    entity_reg.async_get_or_create(
        "sensor",
        "powerwall",
        "battery",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_BATTERY,
    )
    light = entity_reg.async_get_or_create(
        "light", "powerwall", "demo", device_id=device_entry.id
    )

    # Delete the device to make sure we fallback
    # to using the platform
    device_reg.async_remove_device(device_entry.id)

   .opp.states.async_set(light.entity_id, STATE_ON)
   .opp.states.async_set("light.two", STATE_ON)

    def _mock_get_accessory(*args, **kwargs):
        return [None, "acc", None]

    with patch.object(homekit.bridge, "add_accessory"), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ), patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        await homekit.async_start()
    await opp.async_block_till_done()

    mock_get_acc.assert_any_call(
        opp,
        hk_driver,
        ANY,
        ANY,
        {
            "platform": "Tesla Powerwall",
            "linked_battery_charging_sensor": "binary_sensor.powerwall_battery_charging",
            "linked_battery_sensor": "sensor.powerwall_battery",
        },
    )


async def test_homekit_finds_linked_motion_sensors(
    opp, hk_driver, device_reg, entity_reg, mock_zeroconf
):
    """Test HomeKit start method."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {"camera.camera_demo": {}},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = hk_driver
    # pylint: disable=protected-access
    homekit._filter = Mock(return_value=True)
    homekit.bridge = HomeBridge.opp, hk_driver, "mock_bridge")

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        sw_version="0.16.0",
        model="Camera Server",
        manufacturer="Ubq",
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    binary_motion_sensor = entity_reg.async_get_or_create(
        "binary_sensor",
        "camera",
        "motion_sensor",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_MOTION,
    )
    camera = entity_reg.async_get_or_create(
        "camera", "camera", "demo", device_id=device_entry.id
    )

   .opp.states.async_set(
        binary_motion_sensor.entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION},
    )
   .opp.states.async_set(camera.entity_id, STATE_ON)

    def _mock_get_accessory(*args, **kwargs):
        return [None, "acc", None]

    with patch.object(homekit.bridge, "add_accessory"), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ), patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        await homekit.async_start()
    await opp.async_block_till_done()

    mock_get_acc.assert_called_with(
        opp,
        hk_driver,
        ANY,
        ANY,
        {
            "manufacturer": "Ubq",
            "model": "Camera Server",
            "sw_version": "0.16.0",
            "linked_motion_sensor": "binary_sensor.camera_motion_sensor",
        },
    )


async def test_homekit_finds_linked_humidity_sensors(
    opp, hk_driver, device_reg, entity_reg, mock_zeroconf
):
    """Test HomeKit start method."""
    entry = await async_init_integration.opp)

    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {"humidifier.humidifier": {}},
        HOMEKIT_MODE_BRIDGE,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.driver = hk_driver
    homekit._filter = Mock(return_value=True)
    homekit.bridge = HomeBridge.opp, hk_driver, "mock_bridge")

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to.opp.opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        sw_version="0.16.1",
        model="Smart Brainy Clever Humidifier",
        manufacturer="Open Peer Power",
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    humidity_sensor = entity_reg.async_get_or_create(
        "sensor",
        "humidifier",
        "humidity_sensor",
        device_id=device_entry.id,
        device_class=DEVICE_CLASS_HUMIDITY,
    )
    humidifier = entity_reg.async_get_or_create(
        "humidifier", "humidifier", "demo", device_id=device_entry.id
    )

   .opp.states.async_set(
        humidity_sensor.entity_id,
        "42",
        {
            ATTR_DEVICE_CLASS: DEVICE_CLASS_HUMIDITY,
            ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
        },
    )
   .opp.states.async_set(humidifier.entity_id, STATE_ON)

    def _mock_get_accessory(*args, **kwargs):
        return [None, "acc", None]

    with patch.object(homekit.bridge, "add_accessory"), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ), patch(f"{PATH_HOMEKIT}.get_accessory") as mock_get_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        await homekit.async_start()
    await opp.async_block_till_done()

    mock_get_acc.assert_called_with(
        opp,
        hk_driver,
        ANY,
        ANY,
        {
            "manufacturer": "Open Peer Power",
            "model": "Smart Brainy Clever Humidifier",
            "sw_version": "0.16.1",
            "linked_humidity_sensor": "sensor.humidifier_humidity_sensor",
        },
    )


async def test_reload.opp, mock_zeroconf):
    """Test we can reload from yaml."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_IMPORT,
        data={CONF_NAME: "reloadable", CONF_PORT: 12345},
        options={},
    )
    entry.add_to.opp.opp)

    with patch(f"{PATH_HOMEKIT}.HomeKit") as mock_homekit:
        mock_homekit.return_value = homekit = Mock()
        type(homekit).async_start = AsyncMock()
        assert await async_setup_component(
            opp, "homekit", {"homekit": {CONF_NAME: "reloadable", CONF_PORT: 12345}}
        )
        await opp.async_block_till_done()

    mock_homekit.assert_any_call(
        opp,
        "reloadable",
        12345,
        None,
        ANY,
        {},
        HOMEKIT_MODE_BRIDGE,
        None,
        entry.entry_id,
    )
    assert mock_homekit().setup.called is True
    yaml_path = os.path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "homekit/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path), patch(
        f"{PATH_HOMEKIT}.HomeKit"
    ) as mock_homekit2, patch.object(homekit.bridge, "add_accessory"), patch(
        f"{PATH_HOMEKIT}.show_setup_message"
    ), patch(
        f"{PATH_HOMEKIT}.get_accessory"
    ), patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ):
        mock_homekit2.return_value = homekit = Mock()
        type(homekit).async_start = AsyncMock()
        await opp.services.async_call(
            "homekit",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    mock_homekit2.assert_any_call(
        opp,
        "reloadable",
        45678,
        None,
        ANY,
        {},
        HOMEKIT_MODE_BRIDGE,
        None,
        entry.entry_id,
    )
    assert mock_homekit2().setup.called is True


def _get_fixtures_base_path():
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


async def test_homekit_start_in_accessory_mode.opp, hk_driver, device_reg):
    """Test HomeKit start method in accessory mode."""
    entry = await async_init_integration.opp)

    pin = b"123-45-678"
    homekit = HomeKit(
        opp,
        None,
        None,
        None,
        {},
        {},
        HOMEKIT_MODE_ACCESSORY,
        advertise_ip=None,
        entry_id=entry.entry_id,
    )
    homekit.bridge = Mock()
    homekit.bridge.accessories = []
    homekit.driver = hk_driver
    # pylint: disable=protected-access
    homekit._filter = Mock(return_value=True)
    homekit.driver.accessory = Accessory(hk_driver, "any")

   .opp.states.async_set("light.demo", "on")

    with patch(f"{PATH_HOMEKIT}.HomeKit.add_bridge_accessory") as mock_add_acc, patch(
        "pyhap.accessory_driver.AccessoryDriver.add_accessory"
    ), patch(f"{PATH_HOMEKIT}.show_setup_message") as mock_setup_msg, patch(
        "pyhap.accessory_driver.AccessoryDriver.start_service"
    ) as hk_driver_start:
        await homekit.async_start()

    await opp.async_block_till_done()
    mock_add_acc.assert_not_called()
    mock_setup_msg.assert_called_with.opp, entry.entry_id, None, pin, ANY)
    assert hk_driver_start.called
    assert homekit.status == STATUS_RUNNING
