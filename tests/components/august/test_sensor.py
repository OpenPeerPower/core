"""The sensor tests for the august platform."""
from openpeerpower.const import ATTR_UNIT_OF_MEASUREMENT, PERCENTAGE, STATE_UNKNOWN
from openpeerpower.helpers import entity_registry as er

from tests.components.august.mocks import (
    _create_august_with_devices,
    _mock_activities_from_fixture,
    _mock_doorbell_from_fixture,
    _mock_doorsense_enabled_august_lock_detail,
    _mock_lock_from_fixture,
)


async def test_create_doorbell(opp):
    """Test creation of a doorbell."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.json")
    await _create_august_with_devices(opp, [doorbell_one])

    sensor_k98gidt45gul_name_battery = opp.states.get(
        "sensor.k98gidt45gul_name_battery"
    )
    assert sensor_k98gidt45gul_name_battery.state == "96"
    assert (
        sensor_k98gidt45gul_name_battery.attributes["unit_of_measurement"] == PERCENTAGE
    )


async def test_create_doorbell_offline(opp):
    """Test creation of a doorbell that is offline."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.offline.json")
    await _create_august_with_devices(opp, [doorbell_one])
    entity_registry = er.async_get(opp)

    sensor_tmt100_name_battery = opp.states.get("sensor.tmt100_name_battery")
    assert sensor_tmt100_name_battery.state == "81"
    assert sensor_tmt100_name_battery.attributes["unit_of_measurement"] == PERCENTAGE

    entry = entity_registry.async_get("sensor.tmt100_name_battery")
    assert entry
    assert entry.unique_id == "tmt100_device_battery"


async def test_create_doorbell_hardwired(opp):
    """Test creation of a doorbell that is hardwired without a battery."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.nobattery.json")
    await _create_august_with_devices(opp, [doorbell_one])

    sensor_tmt100_name_battery = opp.states.get("sensor.tmt100_name_battery")
    assert sensor_tmt100_name_battery is None


async def test_create_lock_with_linked_keypad(opp):
    """Test creation of a lock with a linked keypad that both have a battery."""
    lock_one = await _mock_lock_from_fixture(opp, "get_lock.doorsense_init.json")
    await _create_august_with_devices(opp, [lock_one])
    entity_registry = er.async_get(opp)

    sensor_a6697750d607098bae8d6baa11ef8063_name_battery = opp.states.get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert sensor_a6697750d607098bae8d6baa11ef8063_name_battery.state == "88"
    assert (
        sensor_a6697750d607098bae8d6baa11ef8063_name_battery.attributes[
            "unit_of_measurement"
        ]
        == PERCENTAGE
    )
    entry = entity_registry.async_get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert entry
    assert entry.unique_id == "A6697750D607098BAE8D6BAA11EF8063_device_battery"

    state = opp.states.get("sensor.front_door_lock_keypad_battery")
    assert state.state == "60"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    entry = entity_registry.async_get("sensor.front_door_lock_keypad_battery")
    assert entry
    assert entry.unique_id == "5bc65c24e6ef2a263e1450a8_linked_keypad_battery"


async def test_create_lock_with_low_battery_linked_keypad(opp):
    """Test creation of a lock with a linked keypad that both have a battery."""
    lock_one = await _mock_lock_from_fixture(opp, "get_lock.low_keypad_battery.json")
    await _create_august_with_devices(opp, [lock_one])
    entity_registry = er.async_get(opp)

    sensor_a6697750d607098bae8d6baa11ef8063_name_battery = opp.states.get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert sensor_a6697750d607098bae8d6baa11ef8063_name_battery.state == "88"
    assert (
        sensor_a6697750d607098bae8d6baa11ef8063_name_battery.attributes[
            "unit_of_measurement"
        ]
        == PERCENTAGE
    )
    entry = entity_registry.async_get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert entry
    assert entry.unique_id == "A6697750D607098BAE8D6BAA11EF8063_device_battery"

    state = opp.states.get("sensor.front_door_lock_keypad_battery")
    assert state.state == "10"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    entry = entity_registry.async_get("sensor.front_door_lock_keypad_battery")
    assert entry
    assert entry.unique_id == "5bc65c24e6ef2a263e1450a8_linked_keypad_battery"

    # No activity means it will be unavailable until someone unlocks/locks it
    lock_operator_sensor = entity_registry.async_get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_operator"
    )
    assert (
        lock_operator_sensor.unique_id
        == "A6697750D607098BAE8D6BAA11EF8063_lock_operator"
    )
    assert (
        opp.states.get("sensor.a6697750d607098bae8d6baa11ef8063_name_operator").state
        == STATE_UNKNOWN
    )


async def test_lock_operator_bluetooth(opp):
    """Test operation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(opp)

    activities = await _mock_activities_from_fixture(
        opp, "get_activity.lock_from_bluetooth.json"
    )
    await _create_august_with_devices(opp, [lock_one], activities=activities)

    entity_registry = er.async_get(opp)
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").state
        == "Your favorite elven princess"
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "remote"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "keypad"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "autorelock"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "method"
        ]
        == "mobile"
    )


async def test_lock_operator_keypad(opp):
    """Test operation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(opp)

    activities = await _mock_activities_from_fixture(
        opp, "get_activity.lock_from_keypad.json"
    )
    await _create_august_with_devices(opp, [lock_one], activities=activities)

    entity_registry = er.async_get(opp)
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").state
        == "Your favorite elven princess"
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "remote"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "keypad"
        ]
        is True
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "autorelock"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "method"
        ]
        == "keypad"
    )


async def test_lock_operator_remote(opp):
    """Test operation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(opp)

    activities = await _mock_activities_from_fixture(opp, "get_activity.lock.json")
    await _create_august_with_devices(opp, [lock_one], activities=activities)

    entity_registry = er.async_get(opp)
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").state
        == "Your favorite elven princess"
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "remote"
        ]
        is True
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "keypad"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "autorelock"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "method"
        ]
        == "remote"
    )


async def test_lock_operator_autorelock(opp):
    """Test operation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(opp)

    activities = await _mock_activities_from_fixture(
        opp, "get_activity.lock_from_autorelock.json"
    )
    await _create_august_with_devices(opp, [lock_one], activities=activities)

    entity_registry = er.async_get(opp)
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").state
        == "Auto Relock"
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "remote"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "keypad"
        ]
        is False
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "autorelock"
        ]
        is True
    )
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").attributes[
            "method"
        ]
        == "autorelock"
    )
