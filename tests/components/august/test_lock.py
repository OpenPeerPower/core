"""The lock tests for the august platform."""

from openpeerpower.components.lock import DOMAIN as LOCK_DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    STATE_LOCKED,
    STATE_UNKNOWN,
    STATE_UNLOCKED,
)

from tests.components.august.mocks import (
    _create_august_with_devices,
    _mock_activities_from_fixture,
    _mock_doorsense_enabled_august_lock_detail,
    _mock_lock_from_fixture,
)


async def test_lock_device_registry.opp):
    """Test creation of a lock with doorsense and bridge ands up in the registry."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail.opp)
    await _create_august_with_devices.opp, [lock_one])

    device_registry = await opp.helpers.device_registry.async_get_registry()

    reg_device = device_registry.async_get_device(
        identifiers={("august", "online_with_doorsense")}
    )
    assert reg_device.model == "AUG-MD01"
    assert reg_device.sw_version == "undefined-4.3.0-1.8.14"
    assert reg_device.name == "online_with_doorsense Name"
    assert reg_device.manufacturer == "August Home Inc."


async def test_lock_changed_by.opp):
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail.opp)

    activities = await _mock_activities_from_fixture.opp, "get_activity.lock.json")
    await _create_august_with_devices.opp, [lock_one], activities=activities)

    lock_online_with_doorsense_name = opp.states.get("lock.online_with_doorsense_name")

    assert lock_online_with_doorsense_name.state == STATE_LOCKED

    assert (
        lock_online_with_doorsense_name.attributes.get("changed_by")
        == "Your favorite elven princess"
    )


async def test_one_lock_operation.opp):
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail.opp)
    await _create_august_with_devices.opp, [lock_one])

    lock_online_with_doorsense_name = opp.states.get("lock.online_with_doorsense_name")

    assert lock_online_with_doorsense_name.state == STATE_LOCKED

    assert lock_online_with_doorsense_name.attributes.get("battery_level") == 92
    assert (
        lock_online_with_doorsense_name.attributes.get("friendly_name")
        == "online_with_doorsense Name"
    )

    data = {ATTR_ENTITY_ID: "lock.online_with_doorsense_name"}
    assert await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True
    )
    await opp.async_block_till_done()

    lock_online_with_doorsense_name = opp.states.get("lock.online_with_doorsense_name")
    assert lock_online_with_doorsense_name.state == STATE_UNLOCKED

    assert lock_online_with_doorsense_name.attributes.get("battery_level") == 92
    assert (
        lock_online_with_doorsense_name.attributes.get("friendly_name")
        == "online_with_doorsense Name"
    )

    assert await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True
    )
    await opp.async_block_till_done()

    lock_online_with_doorsense_name = opp.states.get("lock.online_with_doorsense_name")
    assert lock_online_with_doorsense_name.state == STATE_LOCKED

    # No activity means it will be unavailable until the activity feed has data
    entity_registry = await opp.helpers.entity_registry.async_get_registry()
    lock_operator_sensor = entity_registry.async_get(
        "sensor.online_with_doorsense_name_operator"
    )
    assert lock_operator_sensor
    assert (
        opp.states.get("sensor.online_with_doorsense_name_operator").state
        == STATE_UNKNOWN
    )


async def test_one_lock_unknown_state.opp):
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_lock_from_fixture(
        opp.
        "get_lock.online.unknown_state.json",
    )
    await _create_august_with_devices.opp, [lock_one])

    lock_brokenid_name = opp.states.get("lock.brokenid_name")

    assert lock_brokenid_name.state == STATE_UNKNOWN
