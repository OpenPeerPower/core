"""The tests for the MQTT discovery."""
import copy
import json
from unittest.mock import patch

from openpeerpower.components.tasmota.const import DEFAULT_PREFIX
from openpeerpower.components.tasmota.discovery import ALREADY_DISCOVERED
from openpeerpower.helpers import device_registry as dr

from .conftest import setup_tasmota_helper
from .test_common import DEFAULT_CONFIG, DEFAULT_CONFIG_9_0_0_3

from tests.common import async_fire_mqtt_message


async def test_subscribing_config_topic(opp, mqtt_mock, setup_tasmota):
    """Test setting up discovery."""
    discovery_topic = DEFAULT_PREFIX

    assert mqtt_mock.async_subscribe.called
    call_args = mqtt_mock.async_subscribe.mock_calls[0][1]
    assert call_args[0] == discovery_topic + "/#"
    assert call_args[2] == 0


async def test_future_discovery_message(opp, mqtt_mock, caplog):
    """Test we handle backwards compatible discovery messages."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["future_option"] = "BEST_SINCE_SLICED_BREAD"
    config["so"]["another_future_option"] = "EVEN_BETTER"

    with patch(
        "openpeerpower.components.tasmota.discovery.tasmota_get_device_config",
        return_value={},
    ) as mock_tasmota_get_device_config:
        await setup_tasmota_helper(opp)

        async_fire_mqtt_message(
            opp, f"{DEFAULT_PREFIX}/00000049A3BC/config", json.dumps(config)
        )
        await opp.async_block_till_done()
        assert mock_tasmota_get_device_config.called


async def test_valid_discovery_message(opp, mqtt_mock, caplog):
    """Test discovery callback called."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    with patch(
        "openpeerpower.components.tasmota.discovery.tasmota_get_device_config",
        return_value={},
    ) as mock_tasmota_get_device_config:
        await setup_tasmota_helper(opp)

        async_fire_mqtt_message(
            opp, f"{DEFAULT_PREFIX}/00000049A3BC/config", json.dumps(config)
        )
        await opp.async_block_till_done()
        assert mock_tasmota_get_device_config.called


async def test_invalid_topic(opp, mqtt_mock):
    """Test receiving discovery message on wrong topic."""
    with patch(
        "openpeerpower.components.tasmota.discovery.tasmota_get_device_config"
    ) as mock_tasmota_get_device_config:
        await setup_tasmota_helper(opp)

        async_fire_mqtt_message(opp, f"{DEFAULT_PREFIX}/123456/configuration", "{}")
        await opp.async_block_till_done()
        assert not mock_tasmota_get_device_config.called


async def test_invalid_message(opp, mqtt_mock, caplog):
    """Test receiving an invalid message."""
    with patch(
        "openpeerpower.components.tasmota.discovery.tasmota_get_device_config"
    ) as mock_tasmota_get_device_config:
        await setup_tasmota_helper(opp)

        async_fire_mqtt_message(opp, f"{DEFAULT_PREFIX}/123456/config", "asd")
        await opp.async_block_till_done()
        assert "Invalid discovery message" in caplog.text
        assert not mock_tasmota_get_device_config.called


async def test_invalid_mac(opp, mqtt_mock, caplog):
    """Test topic is not matching device MAC."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    with patch(
        "openpeerpower.components.tasmota.discovery.tasmota_get_device_config"
    ) as mock_tasmota_get_device_config:
        await setup_tasmota_helper(opp)

        async_fire_mqtt_message(
            opp, f"{DEFAULT_PREFIX}/00000049A3BA/config", json.dumps(config)
        )
        await opp.async_block_till_done()
        assert "MAC mismatch" in caplog.text
        assert not mock_tasmota_get_device_config.called


async def test_correct_config_discovery(
    opp, mqtt_mock, caplog, device_reg, entity_reg, setup_tasmota
):
    """Test receiving valid discovery message."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None
    entity_entry = entity_reg.async_get("switch.test")
    assert entity_entry is not None

    state = opp.states.get("switch.test")
    assert state is not None
    assert state.name == "Test"

    assert (mac, "switch", "relay", 0) in opp.data[ALREADY_DISCOVERED]


async def test_device_discover(
    opp, mqtt_mock, caplog, device_reg, entity_reg, setup_tasmota
):
    """Test setting up a device."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None
    assert device_entry.manufacturer == "Tasmota"
    assert device_entry.model == config["md"]
    assert device_entry.name == config["dn"]
    assert device_entry.sw_version == config["sw"]


async def test_device_discover_deprecated(
    opp, mqtt_mock, caplog, device_reg, entity_reg, setup_tasmota
):
    """Test setting up a device with deprecated discovery message."""
    config = copy.deepcopy(DEFAULT_CONFIG_9_0_0_3)
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None
    assert device_entry.manufacturer == "Tasmota"
    assert device_entry.model == config["md"]
    assert device_entry.name == config["dn"]
    assert device_entry.sw_version == config["sw"]


async def test_device_update(
    opp, mqtt_mock, caplog, device_reg, entity_reg, setup_tasmota
):
    """Test updating a device."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["md"] = "Model 1"
    config["dn"] = "Name 1"
    config["sw"] = "v1.2.3.4"
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device entry is created
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None

    # Update device parameters
    config["md"] = "Another model"
    config["dn"] = "Another name"
    config["sw"] = "v6.6.6"

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device entry is updated
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None
    assert device_entry.model == "Another model"
    assert device_entry.name == "Another name"
    assert device_entry.sw_version == "v6.6.6"


async def test_device_remove(
    opp, mqtt_mock, caplog, device_reg, entity_reg, setup_tasmota
):
    """Test removing a discovered device."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device entry is created
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        "",
    )
    await opp.async_block_till_done()

    # Verify device entry is removed
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is None


async def test_device_remove_stale(opp, mqtt_mock, caplog, device_reg, setup_tasmota):
    """Test removing a stale (undiscovered) device does not throw."""
    mac = "00000049A3BC"

    config_entry = opp.config_entries.async_entries("tasmota")[0]

    # Create a device
    device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac)},
    )

    # Verify device entry was created
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None

    # Remove the device
    device_reg.async_remove_device(device_entry.id)

    # Verify device entry is removed
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is None


async def test_device_rediscover(
    opp, mqtt_mock, caplog, device_reg, entity_reg, setup_tasmota
):
    """Test removing a device."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device entry is created
    device_entry1 = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry1 is not None

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        "",
    )
    await opp.async_block_till_done()

    # Verify device entry is removed
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is None

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    # Verify device entry is created, and id is reused
    device_entry = device_reg.async_get_device(
        set(), {(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    assert device_entry is not None
    assert device_entry1.id == device_entry.id


async def test_entity_duplicate_discovery(opp, mqtt_mock, caplog, setup_tasmota):
    """Test entities are not duplicated."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()

    state = opp.states.get("switch.test")
    state_duplicate = opp.states.get("binary_sensor.beer1")

    assert state is not None
    assert state.name == "Test"
    assert state_duplicate is None
    assert (
        f"Entity already added, sending update: switch ('{mac}', 'switch', 'relay', 0)"
        in caplog.text
    )


async def test_entity_duplicate_removal(opp, mqtt_mock, caplog, setup_tasmota):
    """Test removing entity twice."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 1
    mac = config["mac"]

    async_fire_mqtt_message(
        opp,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await opp.async_block_till_done()
    config["rl"][0] = 0
    async_fire_mqtt_message(opp, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await opp.async_block_till_done()
    assert f"Removing entity: switch ('{mac}', 'switch', 'relay', 0)" in caplog.text

    caplog.clear()
    async_fire_mqtt_message(opp, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await opp.async_block_till_done()
    assert "Removing entity: switch" not in caplog.text
