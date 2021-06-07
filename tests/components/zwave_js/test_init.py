"""Test the Z-Wave JS init module."""
from copy import deepcopy
from unittest.mock import call, patch

import pytest
from zwave_js_server.exceptions import BaseZwaveJSServerError, InvalidServerVersion
from zwave_js_server.model.node import Node

from openpeerpower.components.oppio.handler import HassioAPIError
from openpeerpower.components.zwave_js.const import DOMAIN
from openpeerpower.components.zwave_js.helpers import get_device_id
from openpeerpower.config_entries import DISABLED_USER, ConfigEntryState
from openpeerpower.const import STATE_UNAVAILABLE
from openpeerpower.helpers import device_registry as dr, entity_registry as er

from .common import (
    AIR_TEMPERATURE_SENSOR,
    EATON_RF9640_ENTITY,
    NOTIFICATION_MOTION_BINARY_SENSOR,
)

from tests.common import MockConfigEntry


@pytest.fixture(name="connect_timeout")
def connect_timeout_fixture():
    """Mock the connect timeout."""
    with patch("openpeerpower.components.zwave_js.CONNECT_TIMEOUT", new=0) as timeout:
        yield timeout


async def test_entry_setup_unload(opp, client, integration):
    """Test the integration set up and unload."""
    entry = integration

    assert client.connect.call_count == 1
    assert entry.state is ConfigEntryState.LOADED

    await opp.config_entries.async_unload(entry.entry_id)

    assert client.disconnect.call_count == 1
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_open_peer_power_stop(opp, client, integration):
    """Test we clean up on open peer power stop."""
    await opp.async_stop()

    assert client.disconnect.call_count == 1


async def test_initialized_timeout(opp, client, connect_timeout):
    """Test we handle a timeout during client initialization."""
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_enabled_statistics(opp, client):
    """Test that we enabled statistics if the entry is opted in."""
    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org", "data_collection_opted_in": True},
    )
    entry.add_to_opp(opp)

    with patch(
        "zwave_js_server.model.driver.Driver.async_enable_statistics"
    ) as mock_cmd:
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        assert mock_cmd.called


async def test_disabled_statistics(opp, client):
    """Test that we diisabled statistics if the entry is opted out."""
    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org", "data_collection_opted_in": False},
    )
    entry.add_to_opp(opp)

    with patch(
        "zwave_js_server.model.driver.Driver.async_disable_statistics"
    ) as mock_cmd:
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        assert mock_cmd.called


async def test_noop_statistics(opp, client):
    """Test that we don't make any statistics calls if user hasn't provided preference."""
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_opp(opp)

    with patch(
        "zwave_js_server.model.driver.Driver.async_enable_statistics"
    ) as mock_cmd1, patch(
        "zwave_js_server.model.driver.Driver.async_disable_statistics"
    ) as mock_cmd2:
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        assert not mock_cmd1.called
        assert not mock_cmd2.called


@pytest.mark.parametrize("error", [BaseZwaveJSServerError("Boom"), Exception("Boom")])
async def test_listen_failure(opp, client, error):
    """Test we handle errors during client listen."""

    async def listen(driver_ready):
        """Mock the client listen method."""
        # Set the connect side effect to stop an endless loop on reload.
        client.connect.side_effect = BaseZwaveJSServerError("Boom")
        raise error

    client.listen.side_effect = listen
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_on_node_added_ready(opp, multisensor_6_state, client, integration):
    """Test we handle a ready node added event."""
    dev_reg = dr.async_get(opp)
    node = Node(client, multisensor_6_state)
    event = {"node": node}
    air_temperature_device_id = f"{client.driver.controller.home_id}-{node.node_id}"

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert not state  # entity and device not yet added
    assert not dev_reg.async_get_device(
        identifiers={(DOMAIN, air_temperature_device_id)}
    )

    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert state  # entity and device added
    assert state.state != STATE_UNAVAILABLE
    assert dev_reg.async_get_device(identifiers={(DOMAIN, air_temperature_device_id)})


async def test_unique_id_migration_dupes(opp, multisensor_6_state, client, integration):
    """Test we remove an entity when ."""
    ent_reg = er.async_get(opp)

    entity_name = AIR_TEMPERATURE_SENSOR.split(".")[1]

    # Create entity RegistryEntry using old unique ID format
    old_unique_id_1 = (
        f"{client.driver.controller.home_id}.52.52-49-00-Air temperature-00"
    )
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_1,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == AIR_TEMPERATURE_SENSOR
    assert entity_entry.unique_id == old_unique_id_1

    # Create entity RegistryEntry using b0 unique ID format
    old_unique_id_2 = (
        f"{client.driver.controller.home_id}.52.52-49-0-Air temperature-00-00"
    )
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_2,
        suggested_object_id=f"{entity_name}_1",
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == f"{AIR_TEMPERATURE_SENSOR}_1"
    assert entity_entry.unique_id == old_unique_id_2

    # Add a ready node, unique ID should be migrated
    node = Node(client, multisensor_6_state)
    event = {"node": node}

    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    # Check that new RegistryEntry is using new unique ID format
    entity_entry = ent_reg.async_get(AIR_TEMPERATURE_SENSOR)
    new_unique_id = f"{client.driver.controller.home_id}.52-49-0-Air temperature"
    assert entity_entry.unique_id == new_unique_id
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id_1) is None
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id_2) is None


@pytest.mark.parametrize(
    "id",
    [
        ("52.52-49-00-Air temperature-00"),
        ("52.52-49-0-Air temperature-00-00"),
        ("52-49-0-Air temperature-00-00"),
    ],
)
async def test_unique_id_migration(opp, multisensor_6_state, client, integration, id):
    """Test unique ID is migrated from old format to new."""
    ent_reg = er.async_get(opp)

    # Migrate version 1
    entity_name = AIR_TEMPERATURE_SENSOR.split(".")[1]

    # Create entity RegistryEntry using old unique ID format
    old_unique_id = f"{client.driver.controller.home_id}.{id}"
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == AIR_TEMPERATURE_SENSOR
    assert entity_entry.unique_id == old_unique_id

    # Add a ready node, unique ID should be migrated
    node = Node(client, multisensor_6_state)
    event = {"node": node}

    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    # Check that new RegistryEntry is using new unique ID format
    entity_entry = ent_reg.async_get(AIR_TEMPERATURE_SENSOR)
    new_unique_id = f"{client.driver.controller.home_id}.52-49-0-Air temperature"
    assert entity_entry.unique_id == new_unique_id
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id) is None


@pytest.mark.parametrize(
    "id",
    [
        ("32.32-50-00-value-W_Consumed"),
        ("32.32-50-0-value-66049-W_Consumed"),
        ("32-50-0-value-66049-W_Consumed"),
    ],
)
async def test_unique_id_migration_property_key(
    opp, hank_binary_switch_state, client, integration, id
):
    """Test unique ID with property key is migrated from old format to new."""
    ent_reg = er.async_get(opp)

    SENSOR_NAME = "sensor.smart_plug_with_two_usb_ports_value_electric_consumed"
    entity_name = SENSOR_NAME.split(".")[1]

    # Create entity RegistryEntry using old unique ID format
    old_unique_id = f"{client.driver.controller.home_id}.{id}"
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == SENSOR_NAME
    assert entity_entry.unique_id == old_unique_id

    # Add a ready node, unique ID should be migrated
    node = Node(client, hank_binary_switch_state)
    event = {"node": node}

    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    # Check that new RegistryEntry is using new unique ID format
    entity_entry = ent_reg.async_get(SENSOR_NAME)
    new_unique_id = f"{client.driver.controller.home_id}.32-50-0-value-66049"
    assert entity_entry.unique_id == new_unique_id
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id) is None


async def test_unique_id_migration_notification_binary_sensor(
    opp, multisensor_6_state, client, integration
):
    """Test unique ID is migrated from old format to new for a notification binary sensor."""
    ent_reg = er.async_get(opp)

    entity_name = NOTIFICATION_MOTION_BINARY_SENSOR.split(".")[1]

    # Create entity RegistryEntry using old unique ID format
    old_unique_id = f"{client.driver.controller.home_id}.52.52-113-00-Home Security-Motion sensor status.8"
    entity_entry = ent_reg.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        old_unique_id,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
    )
    assert entity_entry.entity_id == NOTIFICATION_MOTION_BINARY_SENSOR
    assert entity_entry.unique_id == old_unique_id

    # Add a ready node, unique ID should be migrated
    node = Node(client, multisensor_6_state)
    event = {"node": node}

    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    # Check that new RegistryEntry is using new unique ID format
    entity_entry = ent_reg.async_get(NOTIFICATION_MOTION_BINARY_SENSOR)
    new_unique_id = f"{client.driver.controller.home_id}.52-113-0-Home Security-Motion sensor status.8"
    assert entity_entry.unique_id == new_unique_id
    assert ent_reg.async_get_entity_id("binary_sensor", DOMAIN, old_unique_id) is None


async def test_old_entity_migration(opp, hank_binary_switch_state, client, integration):
    """Test old entity on a different endpoint is migrated to a new one."""
    node = Node(client, hank_binary_switch_state)

    ent_reg = er.async_get(opp)
    dev_reg = dr.async_get(opp)
    device = dev_reg.async_get_or_create(
        config_entry_id=integration.entry_id, identifiers={get_device_id(client, node)}
    )

    SENSOR_NAME = "sensor.smart_plug_with_two_usb_ports_value_electric_consumed"
    entity_name = SENSOR_NAME.split(".")[1]

    # Create entity RegistryEntry using fake endpoint
    old_unique_id = f"{client.driver.controller.home_id}.32-50-1-value-66049"
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
        device_id=device.id,
    )
    assert entity_entry.entity_id == SENSOR_NAME
    assert entity_entry.unique_id == old_unique_id

    # Do this twice to make sure re-interview doesn't do anything weird
    for i in range(0, 2):
        # Add a ready node, unique ID should be migrated
        event = {"node": node}
        client.driver.controller.emit("node added", event)
        await opp.async_block_till_done()

        # Check that new RegistryEntry is using new unique ID format
        entity_entry = ent_reg.async_get(SENSOR_NAME)
        new_unique_id = f"{client.driver.controller.home_id}.32-50-0-value-66049"
        assert entity_entry.unique_id == new_unique_id
        assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id) is None


async def test_skip_old_entity_migration_for_multiple(
    opp, hank_binary_switch_state, client, integration
):
    """Test that multiple entities of the same value but on a different endpoint get skipped."""
    node = Node(client, hank_binary_switch_state)

    ent_reg = er.async_get(opp)
    dev_reg = dr.async_get(opp)
    device = dev_reg.async_get_or_create(
        config_entry_id=integration.entry_id, identifiers={get_device_id(client, node)}
    )

    SENSOR_NAME = "sensor.smart_plug_with_two_usb_ports_value_electric_consumed"
    entity_name = SENSOR_NAME.split(".")[1]

    # Create two entity entrrys using different endpoints
    old_unique_id_1 = f"{client.driver.controller.home_id}.32-50-1-value-66049"
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_1,
        suggested_object_id=f"{entity_name}_1",
        config_entry=integration,
        original_name=f"{entity_name}_1",
        device_id=device.id,
    )
    assert entity_entry.entity_id == f"{SENSOR_NAME}_1"
    assert entity_entry.unique_id == old_unique_id_1

    # Create two entity entrrys using different endpoints
    old_unique_id_2 = f"{client.driver.controller.home_id}.32-50-2-value-66049"
    entity_entry = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        old_unique_id_2,
        suggested_object_id=f"{entity_name}_2",
        config_entry=integration,
        original_name=f"{entity_name}_2",
        device_id=device.id,
    )
    assert entity_entry.entity_id == f"{SENSOR_NAME}_2"
    assert entity_entry.unique_id == old_unique_id_2
    # Add a ready node, unique ID should be migrated
    event = {"node": node}
    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    # Check that new RegistryEntry is created using new unique ID format
    entity_entry = ent_reg.async_get(SENSOR_NAME)
    new_unique_id = f"{client.driver.controller.home_id}.32-50-0-value-66049"
    assert entity_entry.unique_id == new_unique_id

    # Check that the old entities stuck around because we skipped the migration step
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id_1)
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, old_unique_id_2)


async def test_old_entity_migration_notification_binary_sensor(
    opp, multisensor_6_state, client, integration
):
    """Test old entity on a different endpoint is migrated to a new one for a notification binary sensor."""
    node = Node(client, multisensor_6_state)

    ent_reg = er.async_get(opp)
    dev_reg = dr.async_get(opp)
    device = dev_reg.async_get_or_create(
        config_entry_id=integration.entry_id, identifiers={get_device_id(client, node)}
    )

    entity_name = NOTIFICATION_MOTION_BINARY_SENSOR.split(".")[1]

    # Create entity RegistryEntry using old unique ID format
    old_unique_id = f"{client.driver.controller.home_id}.52-113-1-Home Security-Motion sensor status.8"
    entity_entry = ent_reg.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        old_unique_id,
        suggested_object_id=entity_name,
        config_entry=integration,
        original_name=entity_name,
        device_id=device.id,
    )
    assert entity_entry.entity_id == NOTIFICATION_MOTION_BINARY_SENSOR
    assert entity_entry.unique_id == old_unique_id

    # Do this twice to make sure re-interview doesn't do anything weird
    for _ in range(0, 2):
        # Add a ready node, unique ID should be migrated
        event = {"node": node}
        client.driver.controller.emit("node added", event)
        await opp.async_block_till_done()

        # Check that new RegistryEntry is using new unique ID format
        entity_entry = ent_reg.async_get(NOTIFICATION_MOTION_BINARY_SENSOR)
        new_unique_id = f"{client.driver.controller.home_id}.52-113-0-Home Security-Motion sensor status.8"
        assert entity_entry.unique_id == new_unique_id
        assert (
            ent_reg.async_get_entity_id("binary_sensor", DOMAIN, old_unique_id) is None
        )


async def test_on_node_added_not_ready(opp, multisensor_6_state, client, integration):
    """Test we handle a non ready node added event."""
    dev_reg = dr.async_get(opp)
    node_data = deepcopy(multisensor_6_state)  # Copy to allow modification in tests.
    node = Node(client, node_data)
    node.data["ready"] = False
    event = {"node": node}
    air_temperature_device_id = f"{client.driver.controller.home_id}-{node.node_id}"

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert not state  # entity and device not yet added
    assert not dev_reg.async_get_device(
        identifiers={(DOMAIN, air_temperature_device_id)}
    )

    client.driver.controller.emit("node added", event)
    await opp.async_block_till_done()

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert not state  # entity not yet added but device added in registry
    assert dev_reg.async_get_device(identifiers={(DOMAIN, air_temperature_device_id)})

    node.data["ready"] = True
    node.emit("ready", event)
    await opp.async_block_till_done()

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert state  # entity added
    assert state.state != STATE_UNAVAILABLE


async def test_existing_node_ready(opp, client, multisensor_6, integration):
    """Test we handle a ready node that exists during integration setup."""
    dev_reg = dr.async_get(opp)
    node = multisensor_6
    air_temperature_device_id = f"{client.driver.controller.home_id}-{node.node_id}"

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert state  # entity and device added
    assert state.state != STATE_UNAVAILABLE
    assert dev_reg.async_get_device(identifiers={(DOMAIN, air_temperature_device_id)})


async def test_null_name(opp, client, null_name_check, integration):
    """Test that node without a name gets a generic node name."""
    node = null_name_check
    assert opp.states.get(f"switch.node_{node.node_id}")


async def test_existing_node_not_ready(opp, client, multisensor_6):
    """Test we handle a non ready node that exists during integration setup."""
    dev_reg = dr.async_get(opp)
    node = multisensor_6
    node.data = deepcopy(node.data)  # Copy to allow modification in tests.
    node.data["ready"] = False
    event = {"node": node}
    air_temperature_device_id = f"{client.driver.controller.home_id}-{node.node_id}"
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert not state  # entity not yet added
    assert dev_reg.async_get_device(  # device should be added
        identifiers={(DOMAIN, air_temperature_device_id)}
    )

    node.data["ready"] = True
    node.emit("ready", event)
    await opp.async_block_till_done()

    state = opp.states.get(AIR_TEMPERATURE_SENSOR)

    assert state  # entity and device added
    assert state.state != STATE_UNAVAILABLE
    assert dev_reg.async_get_device(identifiers={(DOMAIN, air_temperature_device_id)})


async def test_start_addon(
    opp, addon_installed, install_addon, addon_options, set_addon_options, start_addon
):
    """Test start the Z-Wave JS add-on during entry setup."""
    device = "/test"
    network_key = "abc123"
    addon_options = {
        "device": device,
        "network_key": network_key,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"use_addon": True, "usb_path": device, "network_key": network_key},
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 0
    assert set_addon_options.call_count == 1
    assert set_addon_options.call_args == call(
        opp, "core_zwave_js", {"options": addon_options}
    )
    assert start_addon.call_count == 1
    assert start_addon.call_args == call(opp, "core_zwave_js")


async def test_install_addon(
    opp, addon_installed, install_addon, addon_options, set_addon_options, start_addon
):
    """Test install and start the Z-Wave JS add-on during entry setup."""
    addon_installed.return_value["version"] = None
    device = "/test"
    network_key = "abc123"
    addon_options = {
        "device": device,
        "network_key": network_key,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"use_addon": True, "usb_path": device, "network_key": network_key},
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 1
    assert install_addon.call_args == call(opp, "core_zwave_js")
    assert set_addon_options.call_count == 1
    assert set_addon_options.call_args == call(
        opp, "core_zwave_js", {"options": addon_options}
    )
    assert start_addon.call_count == 1
    assert start_addon.call_args == call(opp, "core_zwave_js")


@pytest.mark.parametrize("addon_info_side_effect", [HassioAPIError("Boom")])
async def test_addon_info_failure(
    opp,
    addon_installed,
    install_addon,
    addon_options,
    set_addon_options,
    start_addon,
):
    """Test failure to get add-on info for Z-Wave JS add-on during entry setup."""
    device = "/test"
    network_key = "abc123"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"use_addon": True, "usb_path": device, "network_key": network_key},
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 0
    assert start_addon.call_count == 0


@pytest.mark.parametrize(
    "old_device, new_device, old_network_key, new_network_key",
    [("/old_test", "/new_test", "old123", "new123")],
)
async def test_addon_options_changed(
    opp,
    client,
    addon_installed,
    addon_running,
    install_addon,
    addon_options,
    start_addon,
    old_device,
    new_device,
    old_network_key,
    new_network_key,
):
    """Test update config entry data on entry setup if add-on options changed."""
    addon_options["device"] = new_device
    addon_options["network_key"] = new_network_key
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "url": "ws://host1:3001",
            "use_addon": True,
            "usb_path": old_device,
            "network_key": old_network_key,
        },
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state == ConfigEntryState.LOADED
    assert entry.data["usb_path"] == new_device
    assert entry.data["network_key"] == new_network_key
    assert install_addon.call_count == 0
    assert start_addon.call_count == 0


@pytest.mark.parametrize(
    "addon_version, update_available, update_calls, snapshot_calls, "
    "update_addon_side_effect, create_shapshot_side_effect",
    [
        ("1.0", True, 1, 1, None, None),
        ("1.0", False, 0, 0, None, None),
        ("1.0", True, 1, 1, HassioAPIError("Boom"), None),
        ("1.0", True, 0, 1, None, HassioAPIError("Boom")),
    ],
)
async def test_update_addon(
    opp,
    client,
    addon_info,
    addon_installed,
    addon_running,
    create_shapshot,
    update_addon,
    addon_options,
    addon_version,
    update_available,
    update_calls,
    snapshot_calls,
    update_addon_side_effect,
    create_shapshot_side_effect,
):
    """Test update the Z-Wave JS add-on during entry setup."""
    device = "/test"
    network_key = "abc123"
    addon_options["device"] = device
    addon_options["network_key"] = network_key
    addon_info.return_value["version"] = addon_version
    addon_info.return_value["update_available"] = update_available
    create_shapshot.side_effect = create_shapshot_side_effect
    update_addon.side_effect = update_addon_side_effect
    client.connect.side_effect = InvalidServerVersion("Invalid version")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "url": "ws://host1:3001",
            "use_addon": True,
            "usb_path": device,
            "network_key": network_key,
        },
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert create_shapshot.call_count == snapshot_calls
    assert update_addon.call_count == update_calls


@pytest.mark.parametrize(
    "stop_addon_side_effect, entry_state",
    [
        (None, ConfigEntryState.NOT_LOADED),
        (HassioAPIError("Boom"), ConfigEntryState.LOADED),
    ],
)
async def test_stop_addon(
    opp,
    client,
    addon_installed,
    addon_running,
    addon_options,
    stop_addon,
    stop_addon_side_effect,
    entry_state,
):
    """Test stop the Z-Wave JS add-on on entry unload if entry is disabled."""
    stop_addon.side_effect = stop_addon_side_effect
    device = "/test"
    network_key = "abc123"
    addon_options["device"] = device
    addon_options["network_key"] = network_key
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "url": "ws://host1:3001",
            "use_addon": True,
            "usb_path": device,
            "network_key": network_key,
        },
    )
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    await opp.config_entries.async_set_disabled_by(entry.entry_id, DISABLED_USER)
    await opp.async_block_till_done()

    assert entry.state == entry_state
    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call(opp, "core_zwave_js")


async def test_remove_entry(
    opp, addon_installed, stop_addon, create_shapshot, uninstall_addon, caplog
):
    """Test remove the config entry."""
    # test successful remove without created add-on
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"integration_created_addon": False},
    )
    entry.add_to_opp(opp)
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1

    await opp.config_entries.async_remove(entry.entry_id)

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0

    # test successful remove with created add-on
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"integration_created_addon": True},
    )
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call(opp, "core_zwave_js")
    assert create_shapshot.call_count == 1
    assert create_shapshot.call_args == call(
        opp,
        {"name": "addon_core_zwave_js_1.0", "addons": ["core_zwave_js"]},
        partial=True,
    )
    assert uninstall_addon.call_count == 1
    assert uninstall_addon.call_args == call(opp, "core_zwave_js")
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    stop_addon.reset_mock()
    create_shapshot.reset_mock()
    uninstall_addon.reset_mock()

    # test add-on stop failure
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    stop_addon.side_effect = HassioAPIError()

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call(opp, "core_zwave_js")
    assert create_shapshot.call_count == 0
    assert uninstall_addon.call_count == 0
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to stop the Z-Wave JS add-on" in caplog.text
    stop_addon.side_effect = None
    stop_addon.reset_mock()
    create_shapshot.reset_mock()
    uninstall_addon.reset_mock()

    # test create snapshot failure
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    create_shapshot.side_effect = HassioAPIError()

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call(opp, "core_zwave_js")
    assert create_shapshot.call_count == 1
    assert create_shapshot.call_args == call(
        opp,
        {"name": "addon_core_zwave_js_1.0", "addons": ["core_zwave_js"]},
        partial=True,
    )
    assert uninstall_addon.call_count == 0
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to create a snapshot of the Z-Wave JS add-on" in caplog.text
    create_shapshot.side_effect = None
    stop_addon.reset_mock()
    create_shapshot.reset_mock()
    uninstall_addon.reset_mock()

    # test add-on uninstall failure
    entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    uninstall_addon.side_effect = HassioAPIError()

    await opp.config_entries.async_remove(entry.entry_id)

    assert stop_addon.call_count == 1
    assert stop_addon.call_args == call(opp, "core_zwave_js")
    assert create_shapshot.call_count == 1
    assert create_shapshot.call_args == call(
        opp,
        {"name": "addon_core_zwave_js_1.0", "addons": ["core_zwave_js"]},
        partial=True,
    )
    assert uninstall_addon.call_count == 1
    assert uninstall_addon.call_args == call(opp, "core_zwave_js")
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0
    assert "Failed to uninstall the Z-Wave JS add-on" in caplog.text


async def test_removed_device(opp, client, multiple_devices, integration):
    """Test that the device registry gets updated when a device gets removed."""
    nodes = multiple_devices

    # Verify how many nodes are available
    assert len(client.driver.controller.nodes) == 2

    # Make sure there are the same number of devices
    dev_reg = dr.async_get(opp)
    device_entries = dr.async_entries_for_config_entry(dev_reg, integration.entry_id)
    assert len(device_entries) == 2

    # Check how many entities there are
    ent_reg = er.async_get(opp)
    entity_entries = er.async_entries_for_config_entry(ent_reg, integration.entry_id)
    assert len(entity_entries) == 26

    # Remove a node and reload the entry
    old_node = nodes.pop(13)
    await opp.config_entries.async_reload(integration.entry_id)
    await opp.async_block_till_done()

    # Assert that the node and all of it's entities were removed from the device and
    # entity registry
    device_entries = dr.async_entries_for_config_entry(dev_reg, integration.entry_id)
    assert len(device_entries) == 1
    entity_entries = er.async_entries_for_config_entry(ent_reg, integration.entry_id)
    assert len(entity_entries) == 16
    assert dev_reg.async_get_device({get_device_id(client, old_node)}) is None


async def test_suggested_area(opp, client, eaton_rf9640_dimmer):
    """Test that suggested area works."""
    dev_reg = dr.async_get(opp)
    ent_reg = er.async_get(opp)

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    entity = ent_reg.async_get(EATON_RF9640_ENTITY)
    assert dev_reg.async_get(entity.device_id).area_id is not None
